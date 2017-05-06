import pandas as pd
from django import forms
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from base.ufunc import ds, ts
# from opinion.plan.models import TradingPlan
from data.get_data import GetData
from opinion.group.quest.models import QuestLine


def tools(request):
    """

    :param request:
    :return:
    """
    date = pd.datetime.today().date()

    template = 'base/tools/index.html'

    parameters = dict(
        site_title='Tools - Rivers',
        title='Tools & Process',
        date=ds(date),
    )

    return render(request, template, parameters)


def process(request):
    """
    Daily process index page
    :param request:
    :return:
    """
    date = pd.datetime.today().date()

    template = 'base/process.html'
    parameters = {
        'title': "Trading Process",
        'quests': []
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


class ExcelDataForm(forms.Form):
    symbol = forms.CharField(label='Symbol', max_length=20)
    dates = forms.CharField(label='Excel dates', widget=forms.Textarea)


def excel_date_price(request):
    """
    Export date price for a symbol
    :param request: request
    :return: render
    """
    symbol = ''
    data = pd.Series()
    closes = []
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ExcelDataForm(request.POST)
        # print form.is_valid()
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            symbol = form.cleaned_data['symbol']
            raw_dates = form.cleaned_data['dates']

            dates = raw_dates.split()
            df_stock = GetData.get_stock_data(symbol=symbol, reindex=True)
            df_date = df_stock[df_stock.index.isin(dates)]
            # ts(df_date)

            data = df_date['close']
            closes = '\n'.join(['%.2f' % c for c in data.values])

    else:
        form = ExcelDataForm()

    title = 'Date price data'
    if symbol:
        title += ' %s' % ('<%s>' % symbol)

    template = 'base/excel_date_price/index.html'
    parameters = dict(
        site_title=title,
        title=title,
        form=form,
        symbol=symbol,
        data=data.to_string(),
        closes=closes
    )

    return render(request, template, parameters)
