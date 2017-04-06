from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from opinion.group.market.models import *
from opinion.group.market.report import ReportMarketWeek


def market_profile(request, date):
    """
    Market analysis profile using popular indicators
    It is require create every day before marker open
    :param request: request
    :param date: str
    :return: render
    """
    # market indicator section
    market_indicator = MarketSentiment.objects.get(date=date)
    keys = [
        'fund_cash_ratio', 'fear_greek_index', 'credit_balance',
        'put_call_ratio', 'investor_sentiment', 'futures_trader', 'confidence_index',
        'ted_spread', 'margin_debt', 'market_breadth', 'arms_index',
        'ma200day_pct', 'fair_value_trend',
    ]

    # reverse:
    direct0 = [
        'fund_cash_ratio', 'fear_greek_index', 'credit_balance',
        'put_call_ratio', 'investor_sentiment', 'futures_trader',
        'margin_debt', 'market_breadth', 'fair_value_trend',
    ]
    direct1 = {
        'increase': 1, 'range': 0, 'decrease': -1,
        'greed': 1, 'fear': -1,
        'bullish': 1, 'neutral': 0, 'bearish': -1,
        'overbought': 1, 'fair_value': 0, 'oversold': -1,
    }
    reverse1 = {
        'increase': -1, 'range': 0, 'decrease': 1,
        'overbought': -1, 'fair_value': 0, 'oversold': 1,
    }

    summary0 = {'bullish': 0, 'neutral': 0, 'bearish': 0, 'total': 0}
    for key in keys:
        if key in direct0:
            result = direct1[getattr(market_indicator, key)]
        else:
            result = reverse1[getattr(market_indicator, key)]

        summary0['total'] += result

        if result == 1:
            summary0['bullish'] += 1
        elif result == -1:
            summary0['bearish'] += 1
        else:
            summary0['neutral'] += 1

    # macro valuation section
    try:
        macro_valuation = MarketMonthEco.objects.get(date=date)
    except ObjectDoesNotExist:
        macro_valuation = MarketMonthEco.objects.latest('date')

    keys = ['cli_trend', 'bci_trend', 'market_scenario', 'money_supply']
    result1 = {
        'increase': 1, 'range': 0, 'decrease': -1,
        'positive': 1, 'midly_negative': 0, 'very_negative': -1,
    }
    summary1 = {'bullish': 0, 'neutral': 0, 'bearish': 0, 'total': 0}
    for key in keys:

        result = result1[getattr(macro_valuation, key)]
        summary1['total'] += result

        if result == 1:
            summary1['bullish'] += 1
        elif result == -1:
            summary1['bearish'] += 1
        else:
            summary1['neutral'] += 1

    # market opinion
    market_opinion = MarketMovement.objects.get(date=date)

    keys = [
        'volatility', 'bond', 'commodity', 'currency',
        'current_short_trend', 'current_long_trend'
    ]
    result1 = {
        'high': -1, 'normal': 0, 'low': 1,
        'bullish': 1, 'neutral': 0, 'bearish': -1,
    }
    summary2 = {'bullish': 0, 'neutral': 0, 'bearish': 0, 'total': 0}
    for key in keys:
        result = result1[getattr(market_opinion, key)]

        if key in ('bond', 'commodity'):
            result = -result

        summary2['total'] += result

        if result == 1:
            summary2['bullish'] += 1
        elif result == -1:
            summary2['bearish'] += 1
        else:
            summary2['neutral'] += 1

    if market_opinion.market_indicator > 2:
        summary2['total'] -= 1
        summary2['bearish'] += 1
    elif market_opinion.market_indicator > 0 and market_opinion.extra_attention > 2:
        summary2['neutral'] += 1
    else:
        summary2['total'] += 1
        summary2['bullish'] += 1

    template = 'market/market_profile.html'

    parameters = dict(
        site_title='Market profile',
        title='Market profile',
        date=date,
        market_indicator=market_indicator,
        macro_valuation=macro_valuation,
        market_opinion=market_opinion,
        summary0=summary0,
        summary1=summary1,
        summary2=summary2,
    )

    return render(request, template, parameters)


def market_week_create(request, obj_id):
    """

    :param request:
    :param obj_id:
    :return:
    """
    market_week = MarketWeek.objects.get(id=obj_id)

    template = 'opinion/market/week/link.html'

    parameters = dict(
        site_title='Market week create',
        title='Market week create',
        market_week=market_week
    )

    return render(request, template, parameters)


def market_month_economic_create(request, obj_id):
    """

    :param request:
    :param obj_id:
    :return:
    """
    month_eco = MarketMonthEconomic.objects.get(id=obj_id)

    template = 'opinion/market/month/economic/create.html'

    parameters = dict(
        site_title='Market month economic',
        title='Market month economic',
        month_eco=month_eco,
    )

    return render(request, template, parameters)


def market_month_report(request, obj_id):
    """

    :param request:
    :param obj_id:
    :return:
    """
    month_eco = MarketMonthEconomic.objects.get(id=obj_id)

    start = datetime.date(month_eco.date.year, month_eco.date.month, 1)
    stop = datetime.date(month_eco.date.year, month_eco.date.month + 1, 1)

    market_week = MarketWeek.objects.filter(
        date__range=(start, stop)
    )[0]



    template = 'opinion/market/week/index.html'

    parameters = dict(
        site_title='Market report',
        title='Market report',
        month_eco=month_eco,
    )

    return render(request, template, parameters)


def market_week_report(request, obj_id):
    """

    :param request:
    :param obj_id:
    :return:
    """
    market_week = MarketWeek.objects.get(id=obj_id)

    report_week = ReportMarketWeek(market_week)

    reports = {
        'mutual_fund': {
            'data': report_week.fund.create(),
            'explain': report_week.fund.explain(),
            'fund': report_week.fund.fund,
            'net_cash': report_week.fund.net_cash,
        },
        'commitment': {
            'data': report_week.commitment.create(),
        },
        'etf': {
            'objects': market_week.marketweeketfflow_set.all()
        },
        'relocation': {
            'object': market_week.marketweekrelocation
        },
        'impl_vol': {
            'object': market_week.marketweekimplvol
        },
        'valuation': {
            'object': market_week.marketweekvaluation
        },
        'sentiment': {
            'object': market_week.marketweeksentiment
        },
        'technical': {
            'objects': market_week.marketweektechnical_set.all()
        },
        'country': {
            'objects': market_week.marketweekcountry_set.all()
        },
        'global': {
            'objects': market_week.marketweekglobal_set.all()
        },
        'commodity': {
            'objects': market_week.marketweekcommodity_set.all()
        },
        'indices': {
            'objects': market_week.marketweekindices_set.all()
        },
        'sector': {
            'object': market_week.marketweeksector
        },
        'sectors': {
            'objects': market_week.marketweeksectoritem_set.all()
        },
        'research': {
            'objects': market_week.marketweekresearch_set.all()
        },
        'article': {
            'objects': market_week.marketweekarticle_set.all()
        },
        'eco_day': {
            'objects': market_week.marketdayeconomic_set.all()
        },

    }

    template = 'opinion/market/week/report.html'

    parameters = dict(
        site_title='Market week report',
        title='Market week report',
        market_week=market_week,
        reports=reports
    )

    return render(request, template, parameters)

