from django.db.models import Q
from django.shortcuts import render
from opinion.group.fundamental.models import StockFundamental, StockIndustry


def industry_profile(request, symbol, date):
    """
    Industry analysis profile for certain symbol and date
    usually create when enter position and update only once a week
    :param request: request
    :param symbol: str
    :param date: str
    :return: render
    """
    symbol = symbol.upper()

    # fundamental analysis
    fundamental_opinion = StockFundamental.objects.get(Q(symbol=symbol) & Q(date=date))

    keys5 = [
        'mean_rank', 'ownership_activity', 'guru_trade',
    ]
    keys3 = ['insider_trade', 'short_interest']
    keys1 = [
        'earning_surprise', 'earning_grow', 'dividend_grow', 'pe_ratio_trend',
        'div_yield_trend', 'valuation'
    ]
    results = {
        'buying': 1, 'holding': 0, 'selling': -1,
        'increase': 1, 'range': 0, 'decrease': -1,
        'positive': 1, 'no-surprise': 0, 'negative': -1,
        'cheap': 1, 'normal': 0, 'expensive': -1,
    }

    summary0 = {
        'bullish': {'count': 0, 'score': 0},
        'neutral': {'count': 0, 'score': 0},
        'bearish': {'count': 0, 'score': 0},
        'total': {'count': 0, 'score': 0}
    }

    for key in keys5 + keys3 + keys1:
        if key == 'mean_rank':
            result = getattr(fundamental_opinion, key)
        else:
            result = results[getattr(fundamental_opinion, key)]

            if key in keys5:
                result *= 5
            elif key in keys3:
                result *= 3

        summary0['total']['score'] += result
        summary0['total']['count'] += 1

        if result > 0:
            summary0['bullish']['count'] += 1
            summary0['bullish']['score'] += result
        elif result < 0:
            summary0['bearish']['count'] += 1
            summary0['bearish']['score'] += result
        else:
            summary0['neutral']['count'] += 1
            summary0['neutral']['score'] += result

    # industry analysis
    industry_opinion = StockIndustry.objects.get(Q(symbol=symbol) & Q(date=date))

    keys = [
        'index_trend', 'risk_diff', 'industry_pe',
        'industry_rank', 'industry_fa', 'fair_value'
    ]
    results = {
        'higher': 1, 'range': 0, 'lower': -1,
        'bullish': 1, 'neutral': 0, 'bearish': -1,
        'better': 1, 'average': 0, 'worst': -1,
    }

    summary1 = {'bullish': 0, 'neutral': 0, 'bearish': 0, 'total': 0}
    for key in keys:
        result = results[getattr(industry_opinion, key)]

        if key == 'index_trend' and industry_opinion.isolate:
            result = -result
        elif key in ('risk_diff', 'industry_pe', 'fair_value'):
            result = -result

        summary1['total'] += result

        if result == 1:
            summary1['bullish'] += 1
        elif result == -1:
            summary1['bearish'] += 1
        else:
            summary1['neutral'] += 1

    template = 'opinion/industry_profile.html'

    parameters = dict(
        site_title='Industry profile',
        title='{symbol} Industry profile: {industry}, {sector}'.format(
            symbol=industry_opinion.symbol.upper(),
            industry=industry_opinion.industry,
            sector=industry_opinion.sector
        ),
        symbol=symbol,
        date=date,
        fundamental_opinion=fundamental_opinion,
        industry_opinion=industry_opinion,
        summary0=summary0,
        summary1=summary1
    )

    return render(request, template, parameters)
