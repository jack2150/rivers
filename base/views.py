import pandas as pd
from datetime import datetime
from django import forms
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from base.ufunc import ds, ts
# from opinion.plan.models import TradingPlan
from data.get_data import GetData
from opinion.group.quest.models import QuestLine
from calendar import month_name


MONTHS = [month_name[m + 1][:3].upper() for m in range(12)]


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
    data = []
    dates = []
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

            dates = ['%s' % c.strftime('%Y-%m-%d') for c in df_date.index]
            closes = ['%.2f' % float(c) for c in df_date['close'].values]

            for d, c in zip(dates, closes):
                data.append('%s\t%s\n' % (d, c))
            data = ''.join(data)
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
        data=data,
        closes='\n'.join(closes),
        dates='\n'.join(dates),
    )

    return render(request, template, parameters)


class ExtractTradeForm(forms.Form):
    trade = forms.CharField(
        label='Trade', # widget=forms.Textarea
        # widget=forms.TextInput(attrs={'style': 'width:500px'})
        widget=forms.Textarea(attrs={'style': 'width:500px'})
    )


def extract_trade_butterfly(request):
    """

    :param request:
    :return:
    """
    results = []

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ExtractTradeForm(request.POST)
        # print form.is_valid()
        # check whether it's valid:
        if form.is_valid():
            results = []
            lines = form.cleaned_data['trade'].split('\n')
            for line in lines:
                if len(line) == 0:
                    continue

                line = line.strip()
                data = line.split(' ')

                # core
                side = data[0]
                trade_size = int(data[1])
                spread = data[2]
                symbol = data[3]
                right = int(data[4])
                date_num = '%02d%02d%02d' % (
                    int(data[7]), int(MONTHS.index(data[6].upper()) + 1), int(data[5])
                )
                strike_mix = data[8]
                option = data[9]
                price = float(data[10][1:])

                if len(data) == 12:
                    order = data[11]
                else:
                    order = 'LMT'

                # dates
                today = datetime.today().strftime('%m/%d/%Y')
                date_str = datetime.strptime(date_num, '%y%m%d').strftime('%m/%d/%Y')

                # strikes
                strikes = [s for s in strike_mix.split('/')]

                if side == 'BUY':
                    if spread == 'BUTTERFLY' and len(strikes) == 3:
                        sizes = [s * trade_size for s in [1, -2, 1]]
                    else:
                        raise ValueError('Not butterfly spread!')
                else:
                    if spread == 'BUTTERFLY' and len(strikes) == 3:
                        sizes = [s * trade_size for s in [1, -2, 1]]
                    else:
                        raise ValueError('Not butterfly spread!')

                option_char = option[0]
                strike_obj = [
                    {
                        'strike': strikes[0],
                        'size': sizes[0],
                        'code': str('.%s%s%s%s' % (symbol, date_num, option_char, strikes[0])),
                        'bid': '=RTD("tos.rtd", , "BID", [@Code0])',
                        'ask': '=RTD("tos.rtd", , "ASK", [@Code0])',
                        'mean': '=([@Ask0]+[@Bid0])/2',
                        'diff': '=[@Mean0]-[@Price0]',
                    },
                    {
                        'strike': strikes[1],
                        'size': sizes[1],
                        'code': str('.%s%s%s%s' % (symbol, date_num, option_char, strikes[1])),
                        'bid': '=RTD("tos.rtd", , "BID", [@Code1])',
                        'ask': '=RTD("tos.rtd", , "ASK", [@Code1])',
                        'mean': '=([@Ask1]+[@Bid1])/2',
                        'diff': '=[@Mean1]-[@Price1]',
                    },
                    {
                        'strike': strikes[2],
                        'size': sizes[2],
                        'code': str('.%s%s%s%s' % (symbol, date_num, option_char, strikes[2])),
                        'bid': '=RTD("tos.rtd", , "BID", [@Code2])',
                        'ask': '=RTD("tos.rtd", , "ASK", [@Code2])',
                        'mean': '=([@Ask2]+[@Bid2])/2',
                        'diff': '=[@Mean2]-[@Price2]',
                    },
                ]

                strike_data = []
                for temp in strike_obj:
                    strike_data.append(temp['strike'])
                    strike_data.append(temp['size'])
                    strike_data.append(temp['code'])
                    strike_data.append(temp['bid'])
                    strike_data.append(temp['ask'])
                    strike_data.append(temp['mean'])  # mean
                    strike_data.append(0)  # enter_price, fill yourself
                    strike_data.append(temp['diff'])  # mean

                # after
                strike_data.append(
                    '=([@Multi0]*[@Mean0]+[@Multi1]*[@Mean1]+[@Multi2]*[@Mean2])/[@Size]'
                )  # latest price
                strike_data.append(
                    '=[@CurrentPrice]-[@EnterPrice]'
                )  # diff

                # other excel
                close_price = '=RTD("tos.rtd", , "LAST", [@Symbol])'

                # join & format
                result = [
                    0,  # no.
                    line,
                    side,
                    trade_size,
                    spread,
                    symbol,
                    close_price,
                    right,
                    # ex_date0, today, ex_date1, dte, today, remain
                    date_num, today, date_str, '=[@ExDate1]-[@EnterDate]', '=TODAY()', '=[@ExDate1]-[@Today]',
                    option,
                    price,
                    order,
                ]

                result += strike_data
                result = '\t'.join([str(r) for r in result])

                results.append(result)

            results = '\n'.join(results)
    else:
        form = ExtractTradeForm()

    title = 'Extra trade info - Butterfly'
    template = 'base/extract_trade/butterfly.html'
    parameters = dict(
        site_title=title,
        title=title,
        form=form,
        data=results,
    )

    return render(request, template, parameters)
