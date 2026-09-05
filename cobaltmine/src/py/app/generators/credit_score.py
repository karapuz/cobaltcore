from fastapi import APIRouter, Depends

from app.data.models import User
from app.auth import get_current_user

router = APIRouter()

# Industry weights by sector
INDUSTRY_WEIGHTS = {
    'default': {
        'revenueScale': 15.0,
        'ebitdaMargin': 15.0,
        'fcfToDebt': 25.0,
        'debtToEbitda': 25.0,
        'netDebtToEbitda': 10.0,
        'ebitdaToInterest': 10.0
    }
}


def calculate_factor_score(value, factor_type):
    """Calculate letter score based on factor value and type"""
    if factor_type in ['revenueScale']:
        if value >= 100: return 'AA'
        if value >= 80: return 'A'
        if value >= 60: return 'BBB'
        if value >= 40: return 'BB'
        if value >= 20: return 'B'
        return 'CCC'
    elif factor_type in ['ebitdaMargin']:
        if value >= 25: return 'AA'
        if value >= 20: return 'A'
        if value >= 15: return 'BBB'
        if value >= 10: return 'BB'
        if value >= 5: return 'B'
        return 'CCC'
    elif factor_type in ['fcfToDebt']:
        if value >= 30: return 'A'
        if value >= 20: return 'BBB-'
        if value >= 15: return 'BB+'
        if value >= 10: return 'BB'
        return 'B'
    elif factor_type in ['debtToEbitda', 'netDebtToEbitda']:
        if value <= 1.0: return 'AA'
        if value <= 2.0: return 'A'
        if value <= 3.0: return 'BBB'
        if value <= 4.0: return 'BB'
        if value <= 5.0: return 'B'
        return 'CCC'
    elif factor_type in ['ebitdaToInterest']:
        if value >= 8: return 'AA'
        if value >= 5: return 'A'
        if value >= 3: return 'BBB'
        if value >= 2: return 'BB'
        return 'B'
    return 'BB'


def calculate_compass_rating(factor_scores, weights):
    """Calculate overall Compass rating from factor scores"""
    rating_values = {
        'AAA': 21, 'AA+': 20, 'AA': 19, 'AA-': 18,
        'A+': 17, 'A': 16, 'A-': 15,
        'BBB+': 14, 'BBB': 13, 'BBB-': 12,
        'BB+': 11, 'BB': 10, 'BB-': 9,
        'B+': 8, 'B': 7, 'B-': 6,
        'CCC+': 5, 'CCC': 4, 'CCC-': 3,
        'CC': 2, 'C': 1, 'D': 0
    }
    
    value_ratings = {v: k for k, v in rating_values.items()}
    
    weighted_sum = 0
    total_weight = 0
    
    for factor, score in factor_scores.items():
        if factor in weights:
            weight = weights[factor]
            rating_val = rating_values.get(score, 10)
            weighted_sum += rating_val * weight
            total_weight += weight
    
    if total_weight > 0:
        avg_rating = weighted_sum / total_weight
        closest_val = min(rating_values.values(), key=lambda x: abs(x - avg_rating))
        return value_ratings.get(closest_val, 'BB')
    
    return 'BB'


@router.post("/credit-score/compute")
async def compute_credit_score(
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Compute credit score based on financial inputs.
    Returns detailed factor analysis and final Compass rating.
    """
    sector = request_data.get('sector', 'Industrials')
    industry = request_data.get('industry', 'General')
    financial_data = request_data.get('financialData', {})
    
    # Get industry weights (or use default)
    weights = INDUSTRY_WEIGHTS.get(sector, INDUSTRY_WEIGHTS['default'])
    
    # Calculate weighted metrics (average across time periods)
    def get_weighted_average(key):
        vals = []
        for period in ['trailing12', 'oneYearForward', 'twoYearsForward']:
            val = financial_data.get(f'{key}_{period}')
            if val is not None:
                # Weight: 25% trailing, 50% 1yr forward, 25% 2yr forward
                if period == 'oneYearForward':
                    vals.extend([val, val])  # Double weight for 1yr forward
                else:
                    vals.append(val)
        return sum(vals) / len(vals) if vals else 0
    
    revenue = get_weighted_average('revenueScale')
    ebitda = get_weighted_average('ebitda')
    total_debt = get_weighted_average('totalDebt')
    net_debt = get_weighted_average('netDebt')
    fcf = get_weighted_average('freeCashFlow')
    
    # Calculate derived metrics
    ebitda_margin = (ebitda / revenue * 100) if revenue > 0 else 0
    fcf_to_debt = (fcf / total_debt * 100) if total_debt > 0 else 0
    debt_to_ebitda = (total_debt / ebitda) if ebitda > 0 else 0
    net_debt_to_ebitda = (net_debt / ebitda) if ebitda > 0 else 0
    interest = total_debt * 0.05  # Assume 5% of total debt
    ebitda_to_interest = (ebitda / interest) if interest > 0 else 0
    
    # Calculate factor scores
    factor_scores = {
        'revenueScale': calculate_factor_score(revenue, 'revenueScale'),
        'ebitdaMargin': calculate_factor_score(ebitda_margin, 'ebitdaMargin'),
        'fcfToDebt': calculate_factor_score(fcf_to_debt, 'fcfToDebt'),
        'debtToEbitda': calculate_factor_score(debt_to_ebitda, 'debtToEbitda'),
        'netDebtToEbitda': calculate_factor_score(net_debt_to_ebitda, 'netDebtToEbitda'),
        'ebitdaToInterest': calculate_factor_score(ebitda_to_interest, 'ebitdaToInterest'),
    }
    
    # Calculate overall Compass rating
    compass_rating = calculate_compass_rating(factor_scores, weights)
    
    # Build response
    factors = [
        {
            'name': 'Revenue Scale ($ millions)',
            'weight': f"{weights['revenueScale']:.2f}%",
            'metric': f"${revenue:.2f}M",
            'score': factor_scores['revenueScale']
        },
        {
            'name': 'EBITDA Margin',
            'weight': f"{weights['ebitdaMargin']:.2f}%",
            'metric': f"{ebitda_margin:.0f}%",
            'score': factor_scores['ebitdaMargin']
        },
        {
            'name': 'Free Cash Flow / Debt',
            'weight': f"{weights['fcfToDebt']:.2f}%",
            'metric': f"{fcf_to_debt:.0f}%",
            'score': factor_scores['fcfToDebt']
        },
        {
            'name': 'Total Debt / EBITDA',
            'weight': f"{weights['debtToEbitda']:.2f}%",
            'metric': f"{debt_to_ebitda:.1f} x",
            'score': factor_scores['debtToEbitda']
        },
        {
            'name': 'Net Debt / EBITDA',
            'weight': f"{weights['netDebtToEbitda']:.2f}%",
            'metric': f"{net_debt_to_ebitda:.1f} x",
            'score': factor_scores['netDebtToEbitda']
        },
        {
            'name': 'EBITDA / Interest',
            'weight': f"{weights['ebitdaToInterest']:.2f}%",
            'metric': f"{ebitda_to_interest:.1f} x",
            'score': factor_scores['ebitdaToInterest']
        },
    ]
    
    return {
        'sector': sector,
        'industry': industry,
        'compassRating': compass_rating,
        'factors': factors
    }
