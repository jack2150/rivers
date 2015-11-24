from HTMLParser import HTMLParser
import os
import re
import urllib2
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from pandas_datareader.data import get_data_google, get_data_yahoo
from data.models import Underlying, Treasury
from rivers.settings import QUOTE, BASE_DIR
import numpy as np
import pandas as pd


def web_stock_h5(request, source, symbol):
    """
    Web import into hdf5 db
    :param source: str
    :param request: request
    :param symbol: str
    :return: render
    """
    symbol = symbol.upper()

    # get underlying
    underlying = Underlying.objects.get(symbol=symbol)
    start = underlying.start
    end = underlying.stop

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

    # update symbol stat
    if source == 'google':
        underlying.google = len(df_stock)
    else:
        underlying.yahoo = len(df_stock)

    underlying.save()

    # stocks
    stocks = []
    for i, s in df_stock[::-1].iterrows():
        stocks.append('%-16s | %20.2f | %20.2f | %20.2f | %20.2f | %20d' % (
            i.date(), s['open'], s['high'], s['low'], s['close'], s['volume']
        ))

    # for testing
    # Stock.objects.all().delete()
    template = 'data/web_stock_h5.html'
    parameters = dict(
        site_title='Web import',
        title='{source} Web import: {symbol}'.format(
            source=source.capitalize(), symbol=symbol
        ),
        symbol=symbol.lower(),
        source=source,
        stocks=df_stock.to_string(line_width=600)
    )

    return render(request, template, parameters)


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
                print name

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


def set_underlying(request, symbol, action):
    """
    Set underlying is updated after import stock
    :param request: request
    :param symbol: str
    :param action: str
    :return: redirect
    """
    symbol = symbol.upper()

    underlying = Underlying.objects.get(symbol=symbol)
    if action == 'updated':
        underlying.updated = True
    elif action == 'optionable':
        underlying.optionable = True
    else:
        raise ValueError('Invalid view action')
    underlying.save()

    return redirect(reverse('admin:data_underlying_changelist'))


def import_earning(lines, symbol):
    """
    open read fidelity earning file
    :param lines: list of str
    :param symbol: str
    :return: None
    """
    l = [l for l in lines if 'Estimates by Fiscal Quarter' in l][0]
    l = l[l.find('<tbody>') + 7:l.find('</tbody>')]

    # noinspection PyAbstractClass
    class EarningParser(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)

            self.after_smart_estimate = False
            self.data = list()

            self.temp = list()
            self.start = False

        def handle_data(self, data):
            if self.after_smart_estimate:
                if data.split(' ')[0] in ('Q1', 'Q2', 'Q3', 'Q4'):
                    self.start = True

                if self.start:
                    self.temp.append(data)

                if len(self.temp) == 10:
                    if self.temp[5] and self.temp[9]:
                        self.temp[9] = self.temp[5]

                    if '--' not in self.temp:
                        self.data.append(self.temp)

                    self.temp = list()
                    self.start = False

            if data == 'SmartEstimate':
                self.after_smart_estimate = True

    p = EarningParser()
    p.feed(l)
    # update and add new
    earnings = list()
    for l in p.data:
        # print l
        e = {k: str(v) for k, v in zip(
            ['report_date', 'actual_date', 'release', 'estimate_eps', 'analysts',
             'adjusted_eps', 'diff', 'hl', 'gaap', 'actual_eps'], l
        )}

        e['quarter'] = e['report_date'].split(' ')[0]
        e['year'] = int(e['report_date'].split(' ')[1])
        e['actual_date'] = pd.datetime.strptime(e['actual_date'], '%m/%d/%y')  # .date()
        e['analysts'] = int(e['analysts'][1:-1].replace(' Analysts', ''))
        e['low'] = float(e['hl'].split(' / ')[0])
        e['high'] = float(e['hl'].split(' / ')[1])
        del e['report_date'], e['hl'], e['diff']

        for key in ('estimate_eps', 'adjusted_eps', 'gaap', 'actual_eps'):
            e[key] = float(e[key])

        earnings.append(e)
    if len(earnings):
        db = pd.HDFStore(QUOTE)

        try:
            db.remove('event/earning/%s' % symbol.lower())
        except KeyError:
            pass

        df_earning = pd.DataFrame(earnings, index=range(len(earnings)))
        # print df_earning
        db.append(
            'event/earning/%s' % symbol.lower(), df_earning,
            format='table', data_columns=True, min_itemsize=100
        )
        db.close()

        # update earning
        underlying = Underlying.objects.get(symbol=symbol.upper())
        underlying.earning = len(df_earning)
        underlying.save()


def import_dividend(lines, symbol):
    l = [l for l in lines if 'Dividends by Calendar Quarter of Ex-Dividend Date' in l][0]
    l = l[l.find('<tbody>') + 7:l.find('</tbody>')]

    # noinspection PyAbstractClass
    class DividendParser(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)

            self.after_smart_estimate = False
            self.data = list()

            self.temp = list()
            self.counter = 0

        def handle_data(self, data):
            self.temp.append(data)
            if self.counter < 7:
                self.counter += 1
            else:
                self.data.append(self.temp)
                self.temp = list()
                self.counter = 0

    p = DividendParser()
    p.feed(l)
    dividends = list()
    for l in p.data:
        d = {k: str(v) for k, v in zip(
            ['year', 'quarter', 'announce_date', 'expire_date',
             'record_date', 'payable_date', 'amount', 'dividend_type'], l
        )}

        for date in ('announce_date', 'expire_date', 'record_date', 'payable_date'):
            d[date] = pd.datetime.strptime(d[date], '%m/%d/%Y')

        d['year'] = int(d['year'])
        d['amount'] = float(d['amount'])

        dividends.append(d)
    if len(dividends):
        db = pd.HDFStore(QUOTE)

        try:
            db.remove('event/dividend/%s' % symbol.lower())
        except KeyError:
            pass

        df_dividend = pd.DataFrame(dividends, index=range(len(dividends)))
        # print df_dividend
        db.append(
            'event/dividend/%s' % symbol.lower(), df_dividend,
            format='table', data_columns=True, min_itemsize=100
        )
        db.close()

        # update dividend
        underlying = Underlying.objects.get(symbol=symbol.upper())
        underlying.dividend = len(df_dividend)
        underlying.save()


def html_event_import(request, symbol):
    """
    HTML event import without using form
    :param request: request
    :param symbol: str
    :return: return
    """
    symbol = symbol.upper()
    earning_lines = open(os.path.join(
        BASE_DIR, 'files', 'fidelity', 'earnings',
        '%s _ Earnings - Fidelity.html' % symbol)
    ).readlines()
    import_earning(earning_lines, symbol)

    try:
        dividend_lines = open(os.path.join(
            BASE_DIR, 'files', 'fidelity', 'dividends',
            '%s _ Dividends - Fidelity.html' % symbol)
        ).readlines()
        import_dividend(dividend_lines, symbol)
    except IOError:
        pass

    return redirect('admin:data_underlying_changelist')


class TruncateSymbolForm(forms.Form):
    symbol = forms.CharField(
        label='Symbol', max_length=20,
        widget=forms.HiddenInput(
            attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
        )
    )


def truncate_symbol(request, symbol):
    """
    Truncate all data for a single symbol
    :param request: request
    :param symbol: str
    :return: render
    """
    symbol = symbol.upper()
    stats = None

    if request.method == 'POST':
        form = TruncateSymbolForm(request.POST)

        if form.is_valid():
            db = pd.HDFStore(QUOTE)

            keys = [
                'stock/thinkback/%s', 'stock/google/%s', 'stock/yahoo/%s',
                'option/%s/contract', 'option/%s/raw',
                'event/earning/%s', 'event/dividend/%s',
            ]
            for key in keys:
                try:
                    db.remove(key % symbol.lower())
                except KeyError:
                    pass

            db.close()

            # update underlying
            underlying = Underlying.objects.get(symbol=symbol)
            underlying.thinkback = 0
            underlying.contract = 0
            underlying.option = 0
            underlying.google = 0
            underlying.yahoo = 0
            underlying.earning = 0
            underlying.dividend = 0
            underlying.updated = False
            underlying.optionable = False
            underlying.missing_dates = ''
            underlying.save()

            return redirect(reverse('admin:data_underlying_changelist'))
    else:
        form = TruncateSymbolForm(
            initial={'symbol': symbol}
        )

        db = pd.HDFStore(QUOTE)

        names = ['thinkback', 'google', 'yahoo', 'contract', 'option', 'earning', 'dividend']
        keys = ['stock/thinkback/%s', 'stock/google/%s', 'stock/yahoo/%s',
                'option/%s/contract', 'option/%s/raw',
                'event/earning/%s', 'event/dividend/%s']

        df = {}
        for name, key in zip(names, keys):
            try:
                df[name] = db.select(key % symbol.lower())
            except KeyError:
                df[name] = pd.DataFrame()
        db.close()

        stats = {
            'thinkback': {
                'stock': len(df['thinkback']),
                'start': df['thinkback'].index[0].date() if len(df['thinkback']) else 0,
                'stop': df['thinkback'].index[-1].date() if len(df['thinkback']) else 0
            },
            'option': {
                'contract': len(df['contract']),
                'count': len(df['option'])
            },
            'google': {
                'stock': len(df['google']),
                'start': df['google'].index[0].date() if len(df['google']) else 0,
                'stop': df['google'].index[-1].date() if len(df['google']) else 0,
            },
            'yahoo': {
                'stock': len(df['yahoo']),
                'start': df['yahoo'].index[0].date() if len(df['yahoo']) else 0,
                'stop': df['yahoo'].index[-1].date() if len(df['yahoo']) else 0,
            },
            'event': {
                'earning': len(df['earning']),
                'dividend': len(df['dividend']),
            }
        }

    template = 'data/truncate_symbol.html'
    parameters = dict(
        site_title='Truncate symbol',
        title='Truncate symbol',
        symbol=symbol,
        stats=stats,
        form=form
    )

    return render(request, template, parameters)

# todo: need a dte checker that update all dte into correct days
# todo: need fill missing options