"""
Unit tests for credit_rating — the rating engine.

    python -m unittest test_credit_rating -v

The engine is pure, so nothing here needs a running API, a database, an
entity store, environment variables, or the network. If a test in this
file ever needs any of those, something web-shaped has leaked into the
engine and that is the bug, not the test.
"""

import unittest

from model_data.model_store import (
    DEFAULT_RANGES, DEFAULT_WEIGHTS, DEFAULT_VELOCITY, PILLAR_NAMES,
)
import app.generators.credit_rating as engine
from app.generators.credit_rating import (
    InvalidFinancials,
    Pillar,
    apply_notch,
    blend_basics,
    build_credit_rating,
    build_forecast,
    calculate_dscr,
    calculate_dscr_notch,
    calculate_pillar_values,
    calculate_rank,
    format_pillar_value,
    rank_to_rating,
    score_to_rating,
)

B = 1_000_000_000


def basics(**overrides):
    """
    Complete, plausible financials in absolute currency units.

    Ratios land on round numbers so a failure is readable:
      ebitda_margin   = 30/120 = 0.25
      fcf_debt        = 25/50  = 0.5
      td_ebitda       = 60/30  = 2.0
      nd_ebitda       = 45/30  = 1.5
      ebitda_interest = 30/3   = 10.0
      dscr            = 28/(10+50) = 0.4667
    """
    values = {
        "revenue": 120.0 * B,
        "ebitda": 30.0 * B,
        "free_cash_flow": 25.0 * B,
        "debt": 50.0 * B,
        "total_debt": 60.0 * B,
        "net_debt": 45.0 * B,
        "interest": 3.0 * B,
        "operating_cash_flow": 28.0 * B,
        "short_term_debt": 10.0 * B,
    }
    values.update(overrides)
    return values


FLAT = dict.fromkeys(DEFAULT_VELOCITY, 1.0)   # no growth; forecasts == actual


# ─────────────────────────────────────
# Ranking primitives
# ─────────────────────────────────────

class TestCalculateRank(unittest.TestCase):

    def test_increasing_pillar(self):
        bps = [0.35, 0.30, 0.25, 0.20, 0.15, 0.10, 0.05, 0.02]
        self.assertEqual(calculate_rank(0.40, bps, True), 0)
        self.assertEqual(calculate_rank(0.35, bps, True), 0, "boundary is inclusive")
        self.assertEqual(calculate_rank(0.34, bps, True), 1)
        self.assertEqual(calculate_rank(0.01, bps, True), 8, "below every breakpoint")

    def test_decreasing_pillar(self):
        bps = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        self.assertEqual(calculate_rank(0.5, bps, False), 0)
        self.assertEqual(calculate_rank(1.0, bps, False), 0, "boundary is inclusive")
        self.assertEqual(calculate_rank(1.1, bps, False), 1)
        self.assertEqual(calculate_rank(99.0, bps, False), 8)

    def test_rank_never_exceeds_breakpoint_count(self):
        bps = [10, 5, 1]
        self.assertEqual(calculate_rank(-1000, bps, True), 3)


class TestRankToRating(unittest.TestCase):

    def test_known_ranks(self):
        self.assertEqual(rank_to_rating(0), "AAA")
        self.assertEqual(rank_to_rating(2), "AA")
        self.assertEqual(rank_to_rating(8), "BBB")

    def test_out_of_range_clamps(self):
        self.assertEqual(rank_to_rating(-3), "AAA")
        self.assertEqual(rank_to_rating(99), "BBB")

    def test_fractional_rank_is_rejected(self):
        """
        A fractional rank means a caller averaged ranks. The engine blends
        values instead, so this must fail loudly rather than floor silently.
        """
        with self.assertRaises(ValueError) as ctx:
            rank_to_rating(2.45)
        self.assertIn("blend values", str(ctx.exception))

    def test_integer_valued_float_is_accepted(self):
        self.assertEqual(rank_to_rating(3.0), "AA-")


class TestScoreToRating(unittest.TestCase):

    def test_band_edges(self):
        self.assertEqual(score_to_rating(0.0), "AAA")
        self.assertEqual(score_to_rating(1.49), "AAA")
        self.assertEqual(score_to_rating(1.5), "AA+")
        self.assertEqual(score_to_rating(2.5), "AA")

    def test_beyond_the_scale(self):
        self.assertEqual(score_to_rating(100.0), "CC")


class TestApplyNotch(unittest.TestCase):

    def test_positive_notch_worsens(self):
        self.assertEqual(apply_notch("AAA", 1), "AA+")

    def test_negative_notch_improves(self):
        self.assertEqual(apply_notch("AA", -1), "AA+")

    def test_zero_notch_is_identity(self):
        self.assertEqual(apply_notch("BBB", 0), "BBB")

    def test_clamps_at_both_ends(self):
        self.assertEqual(apply_notch("AAA", -5), "AAA")
        self.assertEqual(apply_notch("D", 5), "D")

    def test_unknown_rating_passes_through(self):
        self.assertEqual(apply_notch("ZZZ", 1), "ZZZ")


class TestFormatPillarValue(unittest.TestCase):

    def test_revenue_is_already_in_billions(self):
        """The divisor is applied when the Pillar is built, not here."""
        self.assertEqual(format_pillar_value("revenue_scale", 394.3), "$394.3B")

    def test_ratios_render_as_percent(self):
        self.assertEqual(format_pillar_value("ebitda_margin", 0.331), "33.1%")
        self.assertEqual(format_pillar_value("fcf_debt", 0.896), "89.6%")

    def test_multiples_render_with_x(self):
        self.assertEqual(format_pillar_value("td_ebitda", 0.851), "0.85x")

    def test_undefined_value(self):
        self.assertEqual(format_pillar_value("fcf_debt", None), "n/a")


# ─────────────────────────────────────
# Pillar
# ─────────────────────────────────────

class TestPillar(unittest.TestCase):

    def test_computes_its_own_rank(self):
        p = Pillar("ebitda_margin", 0.33, DEFAULT_RANGES["ebitda_margin"])
        self.assertEqual(p.get_actual_numeric_rank(), 1)
        self.assertEqual(p.get_actual_rating(), "AA+")

    def test_explicit_rank_is_honoured(self):
        """The draft only assigned the rank in the computed branch, so this
        combination raised AttributeError."""
        p = Pillar("fcf_debt", None, DEFAULT_RANGES["fcf_debt"], numeric_rank=0)
        self.assertEqual(p.get_actual_numeric_rank(), 0)
        self.assertEqual(p.get_actual_rating(), "AAA")

    def test_formatted_value_is_a_string_not_a_tuple(self):
        """A stray trailing comma in the draft made this a 1-tuple."""
        p = Pillar("revenue_scale", 394.3, DEFAULT_RANGES["revenue_scale"])
        self.assertIsInstance(p.get_formatted_value(), str)
        self.assertEqual(p.get_formatted_value(), "$394.3B")

    def test_direction_comes_from_the_pillar_id(self):
        self.assertTrue(Pillar("ebitda_interest", 20.0,
                               DEFAULT_RANGES["ebitda_interest"]).get_is_increasing())
        self.assertFalse(Pillar("td_ebitda", 2.0,
                                DEFAULT_RANGES["td_ebitda"]).get_is_increasing())

    def test_none_value_without_rank_is_rejected(self):
        with self.assertRaises(ValueError):
            Pillar("fcf_debt", None, DEFAULT_RANGES["fcf_debt"])

    def test_unknown_pillar_id_is_rejected(self):
        with self.assertRaises(KeyError):
            Pillar("ebtida_margin", 0.3, DEFAULT_RANGES["ebitda_margin"])

    def test_breakpoints_are_copied_not_aliased(self):
        bps = list(DEFAULT_RANGES["td_ebitda"])
        p = Pillar("td_ebitda", 2.0, bps)
        bps[0] = 999
        self.assertEqual(p.get_breakpoints()[0], 1.0)


# ─────────────────────────────────────
# calculate_pillar_values
# ─────────────────────────────────────

class TestCalculatePillarValues(unittest.TestCase):

    def test_returns_the_six_pillars_keyed_by_id(self):
        result = calculate_pillar_values(basics(), DEFAULT_RANGES)
        self.assertEqual(set(result), set(engine.PILLAR_IDS))
        for pillar_id, pillar in result.items():
            self.assertEqual(pillar.get_pillar_id(), pillar_id,
                             "pillar built under the wrong id")

    def test_ebitda_interest_is_not_labelled_nd_ebitda(self):
        """The draft built all three ebitda_interest branches with the id
        'nd_ebitda', giving it the wrong direction, name and format."""
        pillar = calculate_pillar_values(basics(), DEFAULT_RANGES)["ebitda_interest"]
        self.assertEqual(pillar.get_pillar_id(), "ebitda_interest")
        self.assertEqual(pillar.name, PILLAR_NAMES["ebitda_interest"])
        self.assertTrue(pillar.get_is_increasing(), "higher coverage is better")

    def test_ebitda_margin_is_the_ratio_not_raw_ebitda(self):
        """The draft passed `ebitda` where the margin belonged."""
        pillar = calculate_pillar_values(basics(), DEFAULT_RANGES)["ebitda_margin"]
        self.assertAlmostEqual(pillar.get_actual_value(), 0.25)

    def test_revenue_scale_is_converted_to_billions(self):
        pillar = calculate_pillar_values(basics(), DEFAULT_RANGES)["revenue_scale"]
        self.assertAlmostEqual(pillar.get_actual_value(), 120.0)
        self.assertEqual(pillar.get_actual_numeric_rank(), 0)

    def test_all_ratio_values(self):
        result = calculate_pillar_values(basics(), DEFAULT_RANGES)
        self.assertAlmostEqual(result["fcf_debt"].get_actual_value(), 0.5)
        self.assertAlmostEqual(result["td_ebitda"].get_actual_value(), 2.0)
        self.assertAlmostEqual(result["nd_ebitda"].get_actual_value(), 1.5)
        self.assertAlmostEqual(result["ebitda_interest"].get_actual_value(), 10.0)

    def test_leverage_pillars_use_the_right_numerators(self):
        result = calculate_pillar_values(
            basics(total_debt=90.0 * B, net_debt=30.0 * B), DEFAULT_RANGES)
        self.assertAlmostEqual(result["td_ebitda"].get_actual_value(), 3.0)
        self.assertAlmostEqual(result["nd_ebitda"].get_actual_value(), 1.0)

    def test_custom_ranges_change_the_rank_not_the_value(self):
        tight = dict(DEFAULT_RANGES,
                     ebitda_margin=[0.90, 0.80, 0.70, 0.60, 0.50, 0.40, 0.30, 0.20])
        default = calculate_pillar_values(basics(), DEFAULT_RANGES)["ebitda_margin"]
        strict = calculate_pillar_values(basics(), tight)["ebitda_margin"]
        self.assertEqual(default.get_actual_value(), strict.get_actual_value())
        self.assertLess(default.get_actual_numeric_rank(),
                        strict.get_actual_numeric_rank())

    def test_does_not_mutate_its_input(self):
        supplied = basics()
        snapshot = dict(supplied)
        calculate_pillar_values(supplied, DEFAULT_RANGES)
        self.assertEqual(supplied, snapshot)


class TestDegenerateDenominators(unittest.TestCase):
    """
    Undefined ratios are ranked explicitly. A zero ratio is a real, poor
    value; an undefined one can mean best (no debt) or worst (no earnings),
    and the two must not collapse into the same 0.
    """

    def test_no_revenue_is_worst_margin(self):
        pillar = calculate_pillar_values(basics(revenue=0.0), DEFAULT_RANGES)["ebitda_margin"]
        self.assertIsNone(pillar.get_actual_value())
        self.assertEqual(pillar.get_actual_numeric_rank(), 8)

    def test_no_debt_with_positive_fcf_is_best(self):
        pillar = calculate_pillar_values(basics(debt=0.0), DEFAULT_RANGES)["fcf_debt"]
        self.assertEqual(pillar.get_actual_numeric_rank(), 0)

    def test_no_debt_with_negative_fcf_is_worst(self):
        pillar = calculate_pillar_values(
            basics(debt=0.0, free_cash_flow=-5.0 * B), DEFAULT_RANGES)["fcf_debt"]
        self.assertEqual(pillar.get_actual_numeric_rank(), 8)

    def test_no_ebitda_with_debt_is_worst_leverage(self):
        result = calculate_pillar_values(basics(ebitda=0.0), DEFAULT_RANGES)
        self.assertEqual(result["td_ebitda"].get_actual_numeric_rank(), 8)
        self.assertEqual(result["nd_ebitda"].get_actual_numeric_rank(), 8)

    def test_no_ebitda_and_no_debt_is_best_leverage(self):
        result = calculate_pillar_values(
            basics(ebitda=0.0, total_debt=0.0, net_debt=0.0), DEFAULT_RANGES)
        self.assertEqual(result["td_ebitda"].get_actual_numeric_rank(), 0)
        self.assertEqual(result["nd_ebitda"].get_actual_numeric_rank(), 0)

    def test_net_cash_counts_as_no_net_debt(self):
        """net_debt is negative when cash exceeds debt."""
        pillar = calculate_pillar_values(
            basics(ebitda=0.0, net_debt=-20.0 * B), DEFAULT_RANGES)["nd_ebitda"]
        self.assertEqual(pillar.get_actual_numeric_rank(), 0)

    def test_no_interest_with_earnings_is_best_coverage(self):
        """Infinite coverage. The draft had this inverted."""
        pillar = calculate_pillar_values(
            basics(interest=0.0), DEFAULT_RANGES)["ebitda_interest"]
        self.assertEqual(pillar.get_actual_numeric_rank(), 0)

    def test_no_interest_and_no_earnings_is_worst_coverage(self):
        pillar = calculate_pillar_values(
            basics(interest=0.0, ebitda=0.0), DEFAULT_RANGES)["ebitda_interest"]
        self.assertEqual(pillar.get_actual_numeric_rank(), 8)

    def test_negative_ebitda_is_ranked_not_rejected(self):
        result = calculate_pillar_values(basics(ebitda=-15.0 * B), DEFAULT_RANGES)
        self.assertAlmostEqual(result["ebitda_margin"].get_actual_value(), -0.125)
        self.assertEqual(result["ebitda_margin"].get_actual_numeric_rank(), 8)
        self.assertEqual(result["td_ebitda"].get_actual_numeric_rank(), 0,
                         "negative multiple passes the <= test at the first bucket")


class TestInputValidation(unittest.TestCase):

    def test_missing_field_is_rejected(self):
        for field in engine.BASIC_FIELDS:
            with self.subTest(field=field):
                incomplete = basics()
                del incomplete[field]
                with self.assertRaises(InvalidFinancials):
                    calculate_pillar_values(incomplete, DEFAULT_RANGES)

    def test_none_value_is_rejected(self):
        """An unavailable figure must not be scored as if it were data."""
        with self.assertRaises(InvalidFinancials):
            calculate_pillar_values(basics(ebitda=None), DEFAULT_RANGES)

    def test_string_value_is_rejected(self):
        with self.assertRaises(InvalidFinancials):
            calculate_pillar_values(basics(revenue="120"), DEFAULT_RANGES)

    def test_empty_input_is_rejected(self):
        with self.assertRaises(InvalidFinancials):
            calculate_pillar_values({}, DEFAULT_RANGES)


# ─────────────────────────────────────
# Forecasting and blending
# ─────────────────────────────────────

class TestBuildForecast(unittest.TestCase):

    def test_one_year_applies_velocity_once(self):
        result = build_forecast(basics(), 1, DEFAULT_VELOCITY)
        self.assertAlmostEqual(result["revenue"], 120.0 * B * 1.03)

    def test_two_years_compounds(self):
        result = build_forecast(basics(), 2, DEFAULT_VELOCITY)
        self.assertAlmostEqual(result["revenue"], 120.0 * B * 1.03 ** 2)

    def test_flat_velocity_is_the_identity(self):
        self.assertEqual(build_forecast(basics(), 2, FLAT), basics())

    def test_every_field_is_projected(self):
        result = build_forecast(basics(), 1, DEFAULT_VELOCITY)
        self.assertEqual(set(result), set(basics()))


class TestBlendBasics(unittest.TestCase):

    def test_flat_velocity_leaves_figures_unchanged(self):
        """With no growth the three horizons are identical, so a blend
        summing to 1.0 must return the actuals."""
        blended = blend_basics(basics(), FLAT)
        for field, value in basics().items():
            self.assertAlmostEqual(blended[field], value, msg=field)

    def test_matches_the_explicit_weighted_sum(self):
        actual = basics()
        blended = blend_basics(actual, DEFAULT_VELOCITY)
        expected = (actual["revenue"] * 0.55
                    + actual["revenue"] * 1.03 * 0.35
                    + actual["revenue"] * 1.03 ** 2 * 0.10)
        self.assertAlmostEqual(blended["revenue"], expected)

    def test_blend_sits_between_actual_and_two_year_forecast(self):
        actual = basics()
        blended = blend_basics(actual, DEFAULT_VELOCITY)
        two_year = build_forecast(actual, 2, DEFAULT_VELOCITY)
        self.assertGreater(blended["revenue"], actual["revenue"])
        self.assertLess(blended["revenue"], two_year["revenue"])

    def test_a_flat_field_is_untouched_by_the_blend(self):
        """debt has velocity 1.0, so blending cannot move it."""
        blended = blend_basics(basics(), DEFAULT_VELOCITY)
        self.assertAlmostEqual(blended["debt"], basics()["debt"])

    def test_declining_velocity_lowers_the_blend(self):
        shrinking = dict(FLAT, revenue=0.90)
        blended = blend_basics(basics(), shrinking)
        self.assertLess(blended["revenue"], basics()["revenue"])


# ─────────────────────────────────────
# DSCR
# ─────────────────────────────────────

class TestDscr(unittest.TestCase):

    def test_value(self):
        self.assertAlmostEqual(calculate_dscr(basics()), 28.0 / 60.0)

    def test_zero_denominator(self):
        self.assertEqual(calculate_dscr(basics(debt=0.0, short_term_debt=0.0)), 0)

    def test_notch_bands(self):
        self.assertEqual(calculate_dscr_notch(2.0)[0], -1)
        self.assertEqual(calculate_dscr_notch(1.8)[0], -1)
        self.assertEqual(calculate_dscr_notch(1.4)[0], 0)
        self.assertEqual(calculate_dscr_notch(1.0)[0], 0)
        self.assertEqual(calculate_dscr_notch(0.99)[0], 1)


# ─────────────────────────────────────
# build_credit_rating
# ─────────────────────────────────────

class TestBuildCreditRating(unittest.TestCase):

    def test_shape(self):
        result = build_credit_rating(basics())
        for key in ("pillars", "dscr", "base_score", "base_rating",
                    "compass_rating", "score_blend", "blended_basic"):
            self.assertIn(key, result)
        self.assertEqual(len(result["pillars"]), 6)

    def test_pillar_rows_are_in_display_order(self):
        rows = build_credit_rating(basics())["pillars"]
        self.assertEqual([r["id"] for r in rows], list(engine.PILLAR_IDS))

    def test_every_row_carries_actual_forecast_and_blended(self):
        row = build_credit_rating(basics())["pillars"][0]
        for key in ("value", "rank", "forecast_1y_rank", "forecast_2y_rank",
                    "blended_value", "blended_rank", "blended_numeric_rank",
                    "score_contribution"):
            self.assertIn(key, row)

    def test_score_comes_from_blended_ranks(self):
        result = build_credit_rating(basics())
        expected = sum(r["blended_numeric_rank"] * r["weight"]
                       for r in result["pillars"])
        self.assertAlmostEqual(result["base_score"], expected)

    def test_blended_ranks_are_integers(self):
        """Ranking happens once, after blending — so no fractional ranks."""
        for row in build_credit_rating(basics())["pillars"]:
            self.assertEqual(row["blended_numeric_rank"],
                             int(row["blended_numeric_rank"]), row["id"])

    def test_flat_velocity_makes_blended_equal_actual(self):
        result = build_credit_rating(basics(), velocity=FLAT)
        for row in result["pillars"]:
            self.assertEqual(row["blended_numeric_rank"], row["numeric_rank"],
                             row["id"])
            self.assertEqual(row["forecast_2y_rank"], row["rank"], row["id"])

    def test_weights_change_the_score(self):
        """
        Shift weight from revenue_scale (rank 0 here) onto ebitda_margin
        (rank 2). Two pillars sharing a rank would leave the score
        unchanged, which would make this test pass vacuously.
        """
        rows = {r["id"]: r["blended_numeric_rank"]
                for r in build_credit_rating(basics())["pillars"]}
        self.assertNotEqual(rows["revenue_scale"], rows["ebitda_margin"],
                            "fixture no longer exercises reweighting")

        tilted = dict(DEFAULT_WEIGHTS, revenue_scale=0.0, ebitda_margin=0.30)
        base = build_credit_rating(basics())["base_score"]
        tilt = build_credit_rating(basics(), weights=tilted)["base_score"]
        self.assertGreater(tilt, base, "more weight on a worse pillar raises the score")

    def test_total_weight_is_reported(self):
        self.assertAlmostEqual(build_credit_rating(basics())["total_weight"], 1.0)

    def test_notch_is_applied_to_the_final_rating(self):
        """DSCR 0.47 here, below 1.0, so the base rating worsens by one."""
        result = build_credit_rating(basics())
        self.assertEqual(result["dscr"]["notch"], 1)
        self.assertEqual(result["compass_rating"],
                         apply_notch(result["base_rating"], 1))

    def test_strong_dscr_improves_the_rating(self):
        strong = basics(operating_cash_flow=200.0 * B)
        result = build_credit_rating(strong)
        self.assertEqual(result["dscr"]["notch"], -1)

    def test_is_deterministic(self):
        self.assertEqual(build_credit_rating(basics()),
                         build_credit_rating(basics()))

    def test_does_not_mutate_its_inputs(self):
        supplied, ranges, weights, velocity = (
            basics(), dict(DEFAULT_RANGES), dict(DEFAULT_WEIGHTS),
            dict(DEFAULT_VELOCITY))
        snapshots = (dict(supplied), dict(ranges), dict(weights), dict(velocity))
        build_credit_rating(supplied, ranges, weights, velocity)
        self.assertEqual((supplied, ranges, weights, velocity), snapshots)

    def test_rejects_incomplete_financials(self):
        incomplete = basics()
        del incomplete["net_debt"]
        with self.assertRaises(InvalidFinancials):
            build_credit_rating(incomplete)


class TestKnownIssuer(unittest.TestCase):
    """A realistic set, to catch a regression the synthetic cases miss."""

    APPLE = {
        "revenue": 394.3 * B, "ebitda": 130.5 * B, "free_cash_flow": 99.6 * B,
        "debt": 111.1 * B, "total_debt": 111.1 * B, "net_debt": 49.6 * B,
        "interest": 3.9 * B, "operating_cash_flow": 110.5 * B,
        "short_term_debt": 15.0 * B,
    }

    def test_pillar_values(self):
        result = calculate_pillar_values(self.APPLE, DEFAULT_RANGES)
        self.assertAlmostEqual(result["revenue_scale"].get_actual_value(), 394.3)
        self.assertAlmostEqual(result["ebitda_margin"].get_actual_value(), 0.331, places=3)
        self.assertAlmostEqual(result["fcf_debt"].get_actual_value(), 0.896, places=3)
        self.assertAlmostEqual(result["td_ebitda"].get_actual_value(), 0.851, places=3)
        self.assertAlmostEqual(result["nd_ebitda"].get_actual_value(), 0.380, places=3)
        self.assertAlmostEqual(result["ebitda_interest"].get_actual_value(), 33.46, places=2)

    def test_rating(self):
        result = build_credit_rating(self.APPLE)
        self.assertEqual(result["base_rating"], "AAA")
        self.assertEqual(result["dscr"]["notch"], 1, "DSCR 0.88 is below 1.0")
        self.assertEqual(result["compass_rating"], "AA+")


class TestEngineHasNoWebDependencies(unittest.TestCase):
    """
    The split is the point: the engine must stay importable without a web
    stack. This fails the moment someone imports fastapi, a router, the
    entity store or the request-scoped auth helpers into it.
    """

    FORBIDDEN = ("fastapi", "starlette", "uvicorn", "sqlalchemy",
                 "app.auth", "app.routers", "entity_store", "compass_access")

    def test_source_imports_nothing_web_shaped(self):
        import inspect
        source = inspect.getsource(engine)
        for name in self.FORBIDDEN:
            with self.subTest(module=name):
                self.assertNotIn(f"import {name}", source)
                self.assertNotIn(f"from {name}", source)

    def test_module_exposes_no_router(self):
        self.assertFalse(hasattr(engine, "router"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
