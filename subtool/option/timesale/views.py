import logging
import numpy as np
import pandas as pd
from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from rivers.settings import QUOTE_DIR
from subtool.models import OptionTimeSale

logger = logging.getLogger('views')


class OptionTimeSaleForm(forms.Form):
    symbol = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField'}
    ))
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )
    raw_data = forms.CharField(widget=forms.Textarea(
        attrs={'class': 'form-control vLargeTextField'}
    ))

    @staticmethod
    def buy_or_sell(mark, price):
        result = 'unknown'
        if mark > price:
            result = 'SELL'
        elif mark < price:
            result = 'BUY'

        return result

    def process(self):
        """
        Process input raw data into dataframe
        :return: str, pd.DataFrame
        """
        symbol = str(self.cleaned_data['symbol']).upper()
        date = pd.to_datetime(self.cleaned_data['date'])
        lines = self.cleaned_data['raw_data'].split('\n')

        data = []

        for l in lines:
            d = str(l.strip()).split('\t')
            if len(d) == 9:
                d.append('')
            elif len(d) != 10:
                continue

            if len(d[0].split(' ')) == 2:
                d[0] = d[0].split(' ')[1]

            d[2] = d[2].replace(',', '')
            d[1] = d[1] + 'ALL' if d[1][-1] == 'C' else d[1] + 'UT'

            data.append(d)

        df = pd.DataFrame(data, columns=[
            'time', 'option', 'qty', 'price', 'exchange', 'market',
            'delta', 'iv', 'underlying', 'condition'
        ])
        logger.info('df_timesale raw length: %d' % len(df))

        df['price'] = df['price'].astype('float')
        df['qty'] = df['qty'].astype('int')
        df['mark'] = df['market'].apply(
            lambda x: np.mean([float(n) for n in x.split('x')])
        )
        df['trade'] = df.apply(lambda x: self.buy_or_sell(x['mark'], x['price']), axis=1)
        df = df.round({'price': 2, 'mark': 2})

        group = df.group_data(['option', 'trade'])
        df_sum = group.sum()
        df_mean = group.mean()

        df_timesale = pd.concat([df_sum[['qty']], df_mean[['price', 'mark']]], axis=1)
        """:type: pd.DataFrame"""
        logger.info('df_timesale report length: %d' % len(df_timesale))
        df_timesale = df_timesale.reset_index()
        df_timesale = df_timesale[df_timesale['trade'] != 'unknown']

        # df_result['symbol'] = symbol
        df_timesale['date'] = date

        df_timesale = df_timesale[[
            'date', 'option', 'trade', 'qty', 'price', 'mark'
        ]].reset_index(drop=True)
        df_timesale = df_timesale.round({'price': 2, 'mark': 2})

        return symbol, date, df_timesale


def timesale_insert_view(request):
    """
    Insert new option time & sale data and generate report
    :param request: request
    :return: render
    """
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = OptionTimeSaleForm(request.POST)

        if form.is_valid():
            symbol, date, df_timesale = form.process()

            db = pd.HDFStore(QUOTE_DIR)
            path = 'option/%s/final/timesale' % symbol.lower()
            db.append(path, df_timesale, format='table', data_columns=True, min_itemsize=100)
            db.close()

            timesale = OptionTimeSale(
                symbol=symbol.upper(),
                date=date
            )
            timesale.save()

            return redirect(reverse(
                'admin:timesale_report_view', kwargs={
                    'symbol': symbol, 'date': date.strftime('%Y-%m-%d')
                }
            ))
    else:
        form = OptionTimeSaleForm()

    template = 'option/timesale/add.html'

    parameters = dict(
        site_title='Input option time and sale',
        title='Input option time and sale',
        form=form
    )

    return render(request, template, parameters)


def timesale_report_view(request, symbol, date):
    """
    Output option time & sale report for datatable view
    :param request: request
    :param symbol: str
    :param date: str
    :return: render
    """
    db = pd.HDFStore(QUOTE_DIR)
    path = 'option/%s/final/timesale' % symbol.lower()
    df_timesale = db.select(path, where='date == %r' % date)
    db.close()

    df_timesale = df_timesale.sort_values('qty', ascending=False)
    df_timesale = df_timesale[df_timesale['qty'] >= 100]

    timesales = []
    for index, timesale in df_timesale.iterrows():
        data = dict(timesale)
        data['date'] = data['date'].strftime('%Y-%m-%d')
        data['order'] = '%s %+d %s 100 %s @%.2f LMT' % (
            data['trade'].upper(),
            (1 if data['trade'] == 'BUY' else -1) * data['qty'],
            symbol.upper(),
            data['option'],
            data['price']
        )
        timesales.append(data)

    template = 'option/timesale/report.html'

    parameters = dict(
        site_title='Option time and sale summary',
        title='Option time and sale summary',
        timesales=timesales
    )

    return render(request, template, parameters)
