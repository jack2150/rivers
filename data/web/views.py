import logging
import os
import re
import urllib2
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from pandas_datareader.data import get_data_google, get_data_yahoo
import pandas.io.data as web
from data.models import Underlying, Treasury
from rivers.settings import QUOTE_DIR, DB_DIR
import numpy as np
import pandas as pd


logger = logging.getLogger('views')


def web_import(source, symbol, date=''):
    """
    Web import data from google/yahoo
    :param source: str
    :param symbol: str
    :param date: str
    :return: pd.DataFrame
    """
    symbol = symbol.upper()
    # get underlying
    underlying = Underlying.objects.get(symbol=symbol)
    if date != '':
        underlying.stop_date = date
        underlying.save()

    start = underlying.start_date
    end = underlying.stop_date
    # get data function and get data
    if source == 'google':
        use_symbol = underlying.google_symbol if underlying.google_symbol != '' else symbol
        df_stock = get_data_google(symbols=use_symbol, start=start, end=end)
    elif source == 'yahoo':
        use_symbol = underlying.yahoo_symbol if underlying.yahoo_symbol != '' else symbol
        df_stock = get_data_yahoo(symbols=use_symbol, start=start, end=end)
        df_stock['Close'] = df_stock['Adj Close']
        df_stock = df_stock[['Open', 'High', 'Low', 'Close', 'Volume']]
    else:
        raise ValueError('Only google/yahoo web data source')

    # drop if ohlc is empty
    for field in ['Open', 'High', 'Low', 'Close']:
        df_stock[field] = df_stock[field].replace('-', np.nan).astype(float)

    # do not drop if volume is empty
    df_stock['Volume'] = df_stock['Volume'].replace(np.nan, 0).astype(long)
    # df_stock = df_stock[df_stock['Volume'] > 0]  # not drop
    # rename into lower case
    df_stock.columns = [c.lower() for c in df_stock.columns]
    df_stock.index.names = ['date']
    df_stock = df_stock.round({'open': 2, 'high': 2, 'low': 2, 'close': 2})
    # skip or insert
    # z:/quote/aig/data.h5
    path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
    logger.info('Save downloaded data, path: %s' % path)
    db = pd.HDFStore(path)
    if len(df_stock):
        try:
            db.remove('stock/%s' % source)  # remove old
        except KeyError:
            pass
        db.append(
            'stock/%s' % source, df_stock,
            format='table', data_columns=True, min_itemsize=100
        )  # insert new
    db.close()

    return df_stock


def web_stock_h5(request, source, symbol):
    """
    Web import into hdf5 db
    :param source: str
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Web import stock: %s, symbol: %s' % (source.upper(), symbol.upper()))
    df_stock = web_import(source, symbol)

    logger.info('Update underlying status')
    # update symbol stat
    Underlying.write_log(symbol, ['Web %s df_stock: %d' % (source, len(df_stock))])

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))


class TreasuryForm(forms.Form):
    url = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={'class': 'form-control vTextField'})
    )


def web_treasury_h5(request):
    """
    Web import treasury data int db and h5
    :param request: request
    :return: render
    """
    if request.method == 'POST':
        form = TreasuryForm(request.POST)
        if form.is_valid():
            response = urllib2.urlopen(form.cleaned_data['url'])
            html = response.readlines()

            if len(html) < 6:
                raise LookupError('Unable connect to internet or link is invalid')

            data0 = {}
            for i in range(6):
                raw = re.split('(\d+|\w[-.,_:/ A-Za-z0-9]+)', html[i].strip())
                name = raw[1].strip().replace(' ', '_').replace(':', '').lower()

                data0[name] = raw[3]
                if name == 'multiplier':
                    data0[name] = float(raw[3])

            # remove old treasury
            try:
                Treasury.objects.get(time_period=data0['time_period']).delete()
            except ObjectDoesNotExist:
                pass

            # create new treasury
            treasury = Treasury(**data0)

            rate = {'date': [], 'rate': []}
            for i in range(6, len(html)):
                raw = html[i].strip().split(',')
                rate['date'].append(pd.datetime.strptime(raw[0], '%Y-%m-%d'))
                if raw[1] == 'ND':
                    rate['rate'].append(np.nan)
                else:
                    rate['rate'].append(float(raw[1]))

            df_rate = pd.DataFrame(rate).set_index('date').fillna(method='pad')

            # save
            path = os.path.join(DB_DIR, 'treasury.h5')
            logger.info('save treasury data, path: %s' % path)
            db = pd.HDFStore(path)
            # remove old treasury data
            try:
                db.remove('%s' % treasury.to_key())
            except KeyError:
                pass
            # append new treasury data
            db.append(
                '%s' % treasury.to_key(), df_rate,
                format='table', data_columns=True, min_itemsize=100
            )
            db.close()

            treasury.start_date = rate['date'][0]
            treasury.stop_date = rate['date'][-1]

            treasury.save()

            return redirect('admin:data_treasury_changelist')
    else:
        form = TreasuryForm(initial={
            'url': r'http://www.federalreserve.gov/datadownload/Output.aspx?'
                   r'rel=H15&series=e30653a4b627e9d1f2490a0277d9f1ac&lastObs='
                   r'&from=&to=&filetype=csv&label=include&layout=seriescolumn'
        })

    template = 'data/web_treasury_import.html'
    parameters = dict(
        site_title='Treasury import',
        title='Treasury import',
        form=form
    )

    return render(request, template, parameters)


def web_imports(symbols):
    """
    Web import data for each symbols
    :param symbols: list
    :return: None
    """
    date = pd.datetime.today().date().strftime('%Y-%m-%d')
    logger.info('Start update web data: %s' % date)

    for symbol in symbols:
        for source in ('google', 'yahoo'):
            logger.info('Web import: %s, %s, %s' % (source.upper(), symbol.upper(), date))
            web_import(source, symbol, date)
