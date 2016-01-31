import logging
import re
import urllib2
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from pandas_datareader.data import get_data_google, get_data_yahoo
from data.models import Underlying, Treasury
from rivers.settings import QUOTE
import numpy as np
import pandas as pd


logger = logging.getLogger('views')


def web_stock_h5(request, source, symbol):
    """
    Web import into hdf5 db
    :param source: str
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Web import stock: %s, symbol: %s' % (source.upper(), symbol.upper()))
    symbol = symbol.upper()

    # get underlying
    underlying = Underlying.objects.get(symbol=symbol)
    start = underlying.start_date
    end = underlying.stop_date

    # get data function and get data
    f = get_data_google if source == 'google' else get_data_yahoo
    df_stock = f(symbols=symbol, start=start, end=end)

    # drop if ohlc is empty
    for field in ['Open', 'High', 'Low', 'Close']:
        df_stock[field] = df_stock[field].replace('-', np.nan).astype(float)

    # do not drop if volume is empty
    df_stock['Volume'] = df_stock['Volume'].replace('-', 0).astype(long)

    # rename into lower case
    df_stock.columns = [c.lower() for c in df_stock.columns]

    if source == 'yahoo':
        del df_stock['adj close']

    df_stock.index.names = ['date']

    logger.info('Save downloaded data')
    # skip or insert
    db = pd.HDFStore(QUOTE)
    if len(df_stock):
        try:
            db.remove('stock/%s/%s' % (source, symbol.lower()))  # remove old
        except KeyError:
            pass
        db.append(
            'stock/%s/%s' % (source, symbol.lower()), df_stock,
            format='table', data_columns=True, min_itemsize=100
        )  # insert new
    db.close()

    logger.info('Update underlying status')
    # update symbol stat
    underlying.log += 'Web stock imported, source: %s symbol: %s length: %d\n' % (
        source.upper(), symbol.upper(), len(df_stock)
    )
    underlying.save()

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

            db = pd.HDFStore(QUOTE)
            # remove old treasury data
            try:
                db.remove('treasury/%s' % treasury.to_key())
            except KeyError:
                pass
            # append new treasury data
            db.append(
                'treasury/%s' % treasury.to_key(), df_rate,
                format='table', data_columns=True, min_itemsize=100
            )
            db.close()

            treasury.start_date = rate['date'][0]
            treasury.stop_date = rate['date'][-1]

            treasury.save()

            return redirect('admin:data_treasury_changelist')
    else:
        form = TreasuryForm()

    template = 'data/web_treasury_import.html'
    parameters = dict(
        site_title='Treasury import',
        title='Treasury import',
        form=form
    )

    return render(request, template, parameters)
