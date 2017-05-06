from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from opinion.group.market.models import *
from opinion.group.market.report import ReportMarketWeek


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

    template = 'opinion/market/month/economic/link.html'

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

    template = 'opinion/market/month/report.html'

    parameters = dict(
        site_title='Market month report',
        title='Market month report',
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


def market_strategy_report(request, obj_id):
    """

    :param request:
    :param obj_id:
    :return:
    """
    market_strategy = MarketStrategy.objects.get(id=obj_id)

    template = 'opinion/market/strategy/report.html'

    parameters = dict(
        site_title='Market strategy report',
        title='Market strategy report',
        market_strategy=market_strategy,
    )

    return render(request, template, parameters)
