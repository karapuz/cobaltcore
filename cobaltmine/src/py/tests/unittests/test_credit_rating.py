"""
Unit tests for credit_rating — the rating engine.

    python -m unittest test_credit_rating -v

The engine is pure, so nothing here needs a running API, a database, an
entity store, environment variables or the network. If a test in this file
ever needs one of those, something web-shaped has leaked into the engine
and that is the bug, not the test.

Ranks live on the RATING_SCALE axis (AAA=1, AA+=2, AA=3, ...), not in
breakpoint-index space. Several classes below exist specifically to pin
that, because the two scales look alike and every bug in this area so far
has been one being mistaken for the other.
"""

import unittest

from model_data.model_store import (
    BREAKPOINT_TO_RATING,
    DEFAULT_RANGES,
    DEFAULT_VELOCITY,
    DEFAULT_WEIGHTS,
    PILLAR_DIRECTION,
    PILLAR_NAMES,
    RANGE_BREAKPOINTS,
    RATING_SCALE,
)
import app.generators.credit_rating as engine
from app.generators.credit_rating import (
    BEST_RANK,
    WORST_RANK,
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
      revenue_scale   = 120        -> best bucket
      ebitda_margin   = 30/120     = 0.25
      fcf_debt        = 25/50      = 0.5
      td_ebitda       = 60/30      = 2.0
      nd_ebitda       = 45/30      = 1.5
      ebitda_interest = 30/3       = 10.0
      dscr            = 28/(10+50) = 0.467
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


def probe_values(pillar_id):
    """One value per bucket: each breakpoint, then one past the last."""
    bps = DEFAULT_RANGES[pillar_id]
    past = bps[-1] - 1 if PILLAR_DIRECTION[pillar_id] else bps[-1] + 1
    return list(bps) + [past]


# ─────────────────────────────────────
# The rating tables
# ─────────────────────────────────────

class TestRatingTablesAgree(unittest.TestCase):
    """
    BREAKPOINT_TO_RATING carries both a letter and a rank. They must agree
    under score_to_rating, which is the single source of truth for turning
    a number into a letter. Two separate bugs have come from these drifting
    apart, so this is checked directly rather than only through behaviour.
    """

    def test_each_breakpoint_resolves_to_its_own_label(self):
        for index, (letter, rank) in BREAKPOINT_TO_RATING.items():
            with self.subTest(breakpoint=index, letter=letter):
                self.assertEqual(score_to_rating(rank), letter)

    def test_ranks_ascend_with_the_breakpoint_index(self):
        ranks = [rank for _, rank in BREAKPOINT_TO_RATING.values()]
        self.assertEqual(ranks, sorted(ranks))
        self.assertEqual(len(set(ranks)), len(ranks), "duplicate rank")

    def test_best_and_worst_come_from_the_table(self):
        self.assertEqual(BEST_RANK, BREAKPOINT_TO_RATING[min(BREAKPOINT_TO_RATING)][1])
        self.assertEqual(WORST_RANK, BREAKPOINT_TO_RATING[max(BREAKPOINT_TO_RATING)][1])

    def test_worst_rank_is_the_worst_grade_not_a_breakpoint_index(self):
        """
        Returning len(breakpoints) here put a zero-revenue issuer at rank 7,
        which is A- on this scale rather than the worst grade.
        """
        self.assertEqual(score_to_rating(WORST_RANK), RATING_SCALE[-1][0])
        self.assertGreater(WORST_RANK, RANGE_BREAKPOINTS)

    def test_every_default_range_has_the_declared_breakpoint_count(self):
        for pillar_id, breakpoints in DEFAULT_RANGES.items():
            with self.subTest(pillar=pillar_id):
                self.assertEqual(len(breakpoints), RANGE_BREAKPOINTS)

    def test_bucket_count_matches_the_rank_table(self):
        """N breakpoints give N+1 buckets, and each needs its own rank."""
        self.assertEqual(len(BREAKPOINT_TO_RATING), RANGE_BREAKPOINTS + 1)


class TestEveryGradeIsReachable(unittest.TestCase):
    """
    With the ranks one notch off, six of the eight grades became impossible
    to display. Walking the buckets catches that class of error where a
    single spot-check does not.
    """

    EXPECTED = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "CC"]

    def test_each_pillar_walks_the_full_grade_sequence(self):
        for pillar_id in engine.PILLAR_IDS:
            with self.subTest(pillar=pillar_id):
                bps = DEFAULT_RANGES[pillar_id]
                increasing = PILLAR_DIRECTION[pillar_id]
                grades = [rank_to_rating(calculate_rank(v, bps, increasing))
                          for v in probe_values(pillar_id)]
                self.assertEqual(grades, self.EXPECTED)

    def test_buckets_produce_distinct_ranks(self):
        """No two buckets may collapse onto the same rank."""
        for pillar_id in engine.PILLAR_IDS:
            with self.subTest(pillar=pillar_id):
                bps = DEFAULT_RANGES[pillar_id]
                increasing = PILLAR_DIRECTION[pillar_id]
                ranks = [calculate_rank(v, bps, increasing)
                         for v in probe_values(pillar_id)]
                self.assertEqual(len(set(ranks)), len(ranks), ranks)


# ─────────────────────────────────────
# Ranking primitives
# ─────────────────────────────────────

class TestCalculateRank(unittest.TestCase):

    def test_returns_a_rating_scale_rank_not_an_index(self):
        """Second bucket is rank 3 (AA), not index 1."""
        bps = DEFAULT_RANGES["ebitda_margin"]      # [0.5, 0.4, 0.3, ...]
        self.assertEqual(calculate_rank(0.45, bps, True), 3)

    def test_increasing_pillar_boundary_is_inclusive(self):
        bps = DEFAULT_RANGES["ebitda_margin"]
        self.assertEqual(calculate_rank(0.5, bps, True), BEST_RANK)
        self.assertEqual(calculate_rank(0.49, bps, True), 3)

    def test_decreasing_pillar_boundary_is_inclusive(self):
        bps = DEFAULT_RANGES["td_ebitda"]          # [0.5, 1.0, 2.0, ...]
        self.assertEqual(calculate_rank(0.5, bps, False), BEST_RANK)
        self.assertEqual(calculate_rank(0.51, bps, False), 3)

    def test_below_every_breakpoint_is_the_worst_rank(self):
        bps = DEFAULT_RANGES["ebitda_margin"]
        self.assertEqual(calculate_rank(-1.0, bps, True), WORST_RANK)

    def test_above_every_breakpoint_on_a_decreasing_pillar_is_worst(self):
        bps = DEFAULT_RANGES["td_ebitda"]
        self.assertEqual(calculate_rank(999.0, bps, False), WORST_RANK)


class TestRankToRating(unittest.TestCase):

    def test_delegates_to_score_to_rating(self):
        for rank in range(0, WORST_RANK + 1):
            with self.subTest(rank=rank):
                self.assertEqual(rank_to_rating(rank), score_to_rating(rank))

    def test_none_passes_through(self):
        self.assertIsNone(rank_to_rating(None))

    def test_out_of_range_clamps(self):
        self.assertEqual(rank_to_rating(-5), RATING_SCALE[0][0])
        self.assertEqual(rank_to_rating(99), RATING_SCALE[-1][0])

    def test_fractional_rank_is_rejected(self):
        """
        A fractional rank means a caller averaged ranks. The engine blends
        values instead, so this must fail loudly rather than round silently.
        """
        with self.assertRaises(ValueError) as ctx:
            rank_to_rating(2.45)
        self.assertIn("blend values", str(ctx.exception))

    def test_integer_valued_float_is_accepted(self):
        self.assertEqual(rank_to_rating(3.0), "AA")


class TestScoreToRating(unittest.TestCase):

    def test_band_interior_and_edges(self):
        self.assertEqual(score_to_rating(0.0), "AAA")
        self.assertEqual(score_to_rating(1.49), "AAA")
        self.assertEqual(score_to_rating(1.5), "AA+")
        self.assertEqual(score_to_rating(3.0), "AA")

    def test_clamps_at_both_ends(self):
        """A negative score used to return the worst grade."""
        self.assertEqual(score_to_rating(-10.0), "AAA")
        self.assertEqual(score_to_rating(1000.0), RATING_SCALE[-1][0])

    def test_bands_are_contiguous_and_ordered(self):
        for (_, _, high), (_, low, _) in zip(RATING_SCALE, RATING_SCALE[1:]):
            self.assertEqual(high, low, "gap or overlap in RATING_SCALE")


class TestApplyNotch(unittest.TestCase):

    def test_positive_notch_worsens(self):
        self.assertEqual(apply_notch("AA", 1), "AA-")

    def test_negative_notch_improves(self):
        self.assertEqual(apply_notch("AA", -1), "AA+")

    def test_zero_notch_is_identity(self):
        self.assertEqual(apply_notch("BBB", 0), "BBB")

    def test_clamps_at_both_ends(self):
        self.assertEqual(apply_notch("AAA", -5), "AAA")
        self.assertEqual(apply_notch(RATING_SCALE[-1][0], 5), RATING_SCALE[-1][0])

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
        p = Pillar("ebitda_margin", 0.45, DEFAULT_RANGES["ebitda_margin"])
        self.assertEqual(p.get_actual_numeric_rank(), 3)
        self.assertEqual(p.get_actual_rating(), "AA")

    def test_explicit_rank_is_honoured(self):
        p = Pillar("fcf_debt", None, DEFAULT_RANGES["fcf_debt"],
                   numeric_rank=BEST_RANK)
        self.assertEqual(p.get_actual_numeric_rank(), BEST_RANK)
        self.assertEqual(p.get_actual_rating(), "AAA")

    def test_formatted_value_is_a_string_not_a_tuple(self):
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
        original = bps[0]
        bps[0] = 999
        self.assertEqual(p.get_breakpoints()[0], original)


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
        pillar = calculate_pillar_values(basics(), DEFAULT_RANGES)["ebitda_interest"]
        self.assertEqual(pillar.get_pillar_id(), "ebitda_interest")
        self.assertEqual(pillar.name, PILLAR_NAMES["ebitda_interest"])
        self.assertTrue(pillar.get_is_increasing(), "higher coverage is better")

    def test_ebitda_margin_is_the_ratio_not_raw_ebitda(self):
        pillar = calculate_pillar_values(basics(), DEFAULT_RANGES)["ebitda_margin"]
        self.assertAlmostEqual(pillar.get_actual_value(), 0.25)

    def test_revenue_scale_is_converted_to_billions(self):
        pillar = calculate_pillar_values(basics(), DEFAULT_RANGES)["revenue_scale"]
        self.assertAlmostEqual(pillar.get_actual_value(), 120.0)
        self.assertEqual(pillar.get_actual_numeric_rank(), BEST_RANK)

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
                     ebitda_margin=[0.90, 0.80, 0.70, 0.60, 0.50, 0.40, 0.30])
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
    Undefined ratios are ranked explicitly. A ratio of 0 is a real, poor
    value; an undefined one can mean best (no debt) or worst (no earnings),
    and the two must not collapse together.
    """

    def assert_worst(self, pillar):
        self.assertIsNone(pillar.get_actual_value())
        self.assertEqual(pillar.get_actual_numeric_rank(), WORST_RANK)
        self.assertEqual(pillar.get_actual_rating(), RATING_SCALE[-1][0])

    def assert_best(self, pillar):
        self.assertEqual(pillar.get_actual_numeric_rank(), BEST_RANK)
        self.assertEqual(pillar.get_actual_rating(), "AAA")

    def test_no_revenue_is_worst_margin(self):
        self.assert_worst(calculate_pillar_values(
            basics(revenue=0.0), DEFAULT_RANGES)["ebitda_margin"])

    def test_no_debt_with_positive_fcf_is_best(self):
        self.assert_best(calculate_pillar_values(
            basics(debt=0.0), DEFAULT_RANGES)["fcf_debt"])

    def test_no_debt_with_negative_fcf_is_worst(self):
        self.assert_worst(calculate_pillar_values(
            basics(debt=0.0, free_cash_flow=-5.0 * B), DEFAULT_RANGES)["fcf_debt"])

    def test_no_ebitda_with_debt_is_worst_leverage(self):
        result = calculate_pillar_values(basics(ebitda=0.0), DEFAULT_RANGES)
        self.assert_worst(result["td_ebitda"])
        self.assert_worst(result["nd_ebitda"])

    def test_no_ebitda_and_no_debt_is_best_leverage(self):
        result = calculate_pillar_values(
            basics(ebitda=0.0, total_debt=0.0, net_debt=0.0), DEFAULT_RANGES)
        self.assert_best(result["td_ebitda"])
        self.assert_best(result["nd_ebitda"])

    def test_net_cash_counts_as_no_net_debt(self):
        self.assert_best(calculate_pillar_values(
            basics(ebitda=0.0, net_debt=-20.0 * B), DEFAULT_RANGES)["nd_ebitda"])

    def test_no_interest_with_earnings_is_best_coverage(self):
        self.assert_best(calculate_pillar_values(
            basics(interest=0.0), DEFAULT_RANGES)["ebitda_interest"])

    def test_no_interest_and_no_earnings_is_worst_coverage(self):
        self.assert_worst(calculate_pillar_values(
            basics(interest=0.0, ebitda=0.0), DEFAULT_RANGES)["ebitda_interest"])

    def test_negative_ebitda_is_ranked_not_rejected(self):
        result = calculate_pillar_values(basics(ebitda=-15.0 * B), DEFAULT_RANGES)
        self.assertAlmostEqual(result["ebitda_margin"].get_actual_value(), -0.125)
        self.assertEqual(result["ebitda_margin"].get_actual_numeric_rank(),
                         WORST_RANK)


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
        self.assertAlmostEqual(result["revenue"],
                               120.0 * B * DEFAULT_VELOCITY["revenue"])

    def test_two_years_compounds(self):
        result = build_forecast(basics(), 2, DEFAULT_VELOCITY)
        self.assertAlmostEqual(result["revenue"],
                               120.0 * B * DEFAULT_VELOCITY["revenue"] ** 2)

    def test_flat_velocity_is_the_identity(self):
        self.assertEqual(build_forecast(basics(), 2, FLAT), basics())

    def test_every_field_is_projected(self):
        self.assertEqual(set(build_forecast(basics(), 1, DEFAULT_VELOCITY)),
                         set(basics()))


class TestBlendBasics(unittest.TestCase):

    def test_flat_velocity_leaves_figures_unchanged(self):
        """With no growth the horizons are identical, so a blend summing to
        1.0 must return the actuals."""
        blended = blend_basics(basics(), FLAT)
        for field, value in basics().items():
            self.assertAlmostEqual(blended[field], value, msg=field)

    def test_matches_the_explicit_weighted_sum(self):
        actual = basics()
        v = DEFAULT_VELOCITY["revenue"]
        expected = (actual["revenue"] * engine.SCORE_BLEND["actual"]
                    + actual["revenue"] * v * engine.SCORE_BLEND["forecast_1y"]
                    + actual["revenue"] * v ** 2 * engine.SCORE_BLEND["forecast_2y"])
        self.assertAlmostEqual(blend_basics(actual, DEFAULT_VELOCITY)["revenue"],
                               expected)

    def test_blend_sits_between_actual_and_two_year_forecast(self):
        actual = basics()
        blended = blend_basics(actual, DEFAULT_VELOCITY)
        two_year = build_forecast(actual, 2, DEFAULT_VELOCITY)
        self.assertGreater(blended["revenue"], actual["revenue"])
        self.assertLess(blended["revenue"], two_year["revenue"])

    def test_declining_velocity_lowers_the_blend(self):
        blended = blend_basics(basics(), dict(FLAT, revenue=0.90))
        self.assertLess(blended["revenue"], basics()["revenue"])

    def test_blend_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(engine.SCORE_BLEND.values()), 1.0)


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

    def test_notch_reason_is_reported(self):
        self.assertTrue(calculate_dscr_notch(0.5)[1])


# ─────────────────────────────────────
# build_credit_rating
# ─────────────────────────────────────

class TestBuildCreditRating(unittest.TestCase):

    def test_shape(self):
        result = build_credit_rating(basics())
        for key in ("pillars", "dscr", "base_score", "base_rating",
                    "compass_rating", "score_blend", "blended_basic"):
            self.assertIn(key, result)
        self.assertEqual(len(result["pillars"]), len(engine.PILLAR_IDS))

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

    def test_base_score_is_on_the_rating_scale(self):
        """A weighted average of ranks stays inside the rank range."""
        result = build_credit_rating(basics())
        self.assertGreaterEqual(result["base_score"], BEST_RANK)
        self.assertLessEqual(result["base_score"], WORST_RANK)

    def test_weights_change_the_score(self):
        rows = {r["id"]: r["blended_numeric_rank"]
                for r in build_credit_rating(basics())["pillars"]}
        self.assertNotEqual(rows["revenue_scale"], rows["ebitda_margin"],
                            "fixture no longer exercises reweighting")
        tilted = dict(DEFAULT_WEIGHTS, revenue_scale=0.0,
                      ebitda_margin=DEFAULT_WEIGHTS["revenue_scale"]
                      + DEFAULT_WEIGHTS["ebitda_margin"])
        base = build_credit_rating(basics())["base_score"]
        tilt = build_credit_rating(basics(), weights=tilted)["base_score"]
        self.assertGreater(tilt, base,
                           "more weight on a worse pillar must raise the score")

    def test_total_weight_is_reported(self):
        self.assertAlmostEqual(build_credit_rating(basics())["total_weight"], 1.0)

    def test_weak_dscr_worsens_the_final_rating(self):
        result = build_credit_rating(basics())
        self.assertEqual(result["dscr"]["notch"], 1)
        self.assertEqual(result["compass_rating"],
                         apply_notch(result["base_rating"], 1))

    def test_strong_dscr_improves_the_final_rating(self):
        result = build_credit_rating(basics(operating_cash_flow=200.0 * B))
        self.assertEqual(result["dscr"]["notch"], -1)
        self.assertEqual(result["compass_rating"],
                         apply_notch(result["base_rating"], -1))

    def test_is_deterministic(self):
        self.assertEqual(build_credit_rating(basics()),
                         build_credit_rating(basics()))

    def test_does_not_mutate_its_inputs(self):
        supplied = basics()
        ranges = {k: list(v) for k, v in DEFAULT_RANGES.items()}
        weights = dict(DEFAULT_WEIGHTS)
        velocity = dict(DEFAULT_VELOCITY)
        snapshots = (dict(supplied), {k: list(v) for k, v in ranges.items()},
                     dict(weights), dict(velocity))
        build_credit_rating(supplied, ranges, weights, velocity)
        self.assertEqual(supplied, snapshots[0])
        self.assertEqual(ranges, snapshots[1])
        self.assertEqual(weights, snapshots[2])
        self.assertEqual(velocity, snapshots[3])

    def test_rejects_incomplete_financials(self):
        incomplete = basics()
        del incomplete["net_debt"]
        with self.assertRaises(InvalidFinancials):
            build_credit_rating(incomplete)

    def test_worst_case_issuer_rates_at_the_bottom(self):
        """Every pillar undefined and unfavourable."""
        broke = basics(revenue=0.0, ebitda=0.0, free_cash_flow=-1.0 * B,
                       interest=0.0)
        result = build_credit_rating(broke)
        self.assertEqual(result["base_rating"], RATING_SCALE[-1][0])


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

    def test_pillar_grades(self):
        result = calculate_pillar_values(self.APPLE, DEFAULT_RANGES)
        self.assertEqual(
            [result[p].get_actual_rating() for p in engine.PILLAR_IDS],
            ["AAA", "A", "AAA", "AA", "AA", "AA"])

    def test_rating(self):
        result = build_credit_rating(self.APPLE)
        self.assertEqual(result["base_rating"], "AA")
        self.assertEqual(result["dscr"]["notch"], 1, "DSCR 0.88 is below 1.0")
        self.assertEqual(result["compass_rating"], "AA-")


class TestEngineHasNoWebDependencies(unittest.TestCase):
    """
    The split is the point: the engine must stay importable without a web
    stack. This fails the moment someone imports fastapi, a router, the
    entity store or request-scoped auth helpers into it.
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

    def test_no_debug_printing(self):
        """A print in the pillar path emits a line per pillar per request."""
        import inspect
        for line in inspect.getsource(engine).splitlines():
            stripped = line.strip()
            if stripped.startswith("print("):
                self.fail(f"debug print left in the engine: {stripped}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""
python tests/unittests/test_credit_rating.py
"""