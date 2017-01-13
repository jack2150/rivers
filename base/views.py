import pandas as pd
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from base.ufunc import ds
# from opinion.plan.models import TradingPlan
from opinion.group.quest.models import QuestLine


def daily_process_summary(request):
    """
    Daily process view
    :param request: request
    :return: render
    """
    date = pd.datetime.today().date()

    """
    trading_plans = TradingPlan.objects.filter(active=True)
    trading_data = []
    for plan in trading_plans:
        quests = plan.tradingquest_set.filter(achievement__isnull=True)
        trading_data.append((plan, quests))
    """

    template = 'base/daily_process.html'

    parameters = dict(
        site_title='Daily process',
        title='Daily process summary',
        # trading_data=trading_data,
        date=ds(date)
    )

    return render(request, template, parameters)

# todo: cont next


def process(request):
    """
    Daily process index page
    :param request:
    :return:
    """
    date = pd.datetime.today().date()

    quest_lines = QuestLine.objects.filter(active=True)
    quests = []
    for i, quest in enumerate(quest_lines):
        parts = quest.questpart_set.filter(achievement__isnull=True)
        quests.append((i, quest, parts))

    template = 'base/process.html'
    parameters = {
        'title': "Trading Process",
        'quests': quests
    }

    return render(request, template, parameters)


def market(request):
    """
    Daily process index page
    :param request:
    :return:
    """
    template = 'base/market.html'
    parameters = {
        'title': "Market reference",
    }

    return render(request, template, parameters)


@csrf_exempt
def reference(request, symbol=''):
    """
    Daily process index page
    :param symbol: str
    :param request:
    :return:
    """
    if symbol == '':
        symbol = 'SPY'

    template = 'base/reference.html'
    parameters = {
        'title': "%s reference" % symbol.upper(),
        'symbol': symbol.upper()
    }

    return render(request, template, parameters)


def progress(request):
    """

    :param request:
    :return:
    """

    quest_lines = QuestLine.objects.filter(active=True)
    quests = []
    for i, quest in enumerate(quest_lines):
        parts = quest.questpart_set.filter(achievement__isnull=True)
        quests.append((i, quest, parts))

    template = 'base/progress_tracker.html'
    parameters = {
        'title': "Progress tracker",
        'quests': quests
    }

    return render(request, template, parameters)

# todo: cont next, technical for volume weight, momentum agressive, screw squeeze job,