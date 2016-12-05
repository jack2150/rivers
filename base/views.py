import pandas as pd
from django.shortcuts import render

from base.ufunc import ds
from opinion.plan.models import TradingPlan


def daily_process_summary(request):
    """
    Daily process view
    :param request: request
    :return: render
    """
    date = pd.datetime.today().date()
    trading_plans = TradingPlan.objects.filter(active=True)

    trading_data = []
    for plan in trading_plans:
        quests = plan.tradingquest_set.filter(achievement__isnull=True)
        trading_data.append((plan, quests))

    template = 'base/daily_process.html'

    parameters = dict(
        site_title='Daily process',
        title='Daily process summary',
        trading_data=trading_data,
        date=ds(date)
    )

    return render(request, template, parameters)
