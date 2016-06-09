import logging
import os

import pandas as pd
import urllib2
from bs4 import BeautifulSoup
from django import forms
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import render, redirect
from data.models import Underlying, SplitHistory
from data.tb.final.views import reshape_h5
from rivers.settings import QUOTE_DIR


logger = logging.getLogger('views')


def set_underlying(request, symbol, action):
    """
    Set underlying is updated after import stock
    :param request: request
    :param symbol: str
    :param action: str
    :return: redirect
    """
    underlying = Underlying.objects.get(symbol=symbol.upper())
    setattr(underlying, action, not getattr(underlying, action))
    underlying.save()

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))


def update_underlying(request, symbol):
    """
    Download from website then update underlying detail
    :param request: request
    :param symbol: int
    :return: redirect
    """
    underlying = Underlying.objects.get(
        Q(symbol=symbol.upper()) | Q(symbol=symbol.lower())
    )
    underlying.symbol = underlying.symbol.upper()
    logger.info('Underlying: %s, id: %d' % (underlying.symbol, underlying.id))

    url = 'http://finviz.com/quote.ashx?t=%s' % underlying.symbol.lower()
    logger.info('start download: %s' % url)

    req = urllib2.Request(url=url)
    f = urllib2.urlopen(req)
    html = [unicode(l, 'utf-8') for l in f.readlines()]

    logger.info('done download html, data length: %d' % len(html))

    symbol_tag = u'>%s<' % underlying.symbol.upper()
    for i, line in enumerate(html):
        if 'Optionable' in line:
            soup = BeautifulSoup(line, 'html.parser')
            underlying.optionable = True if soup.b.string == 'Yes' else False
            logger.info('optionable: %s' % soup.b.string)
        elif 'Shortable' in line:
            soup = BeautifulSoup(line, 'html.parser')
            underlying.shortable = True if soup.b.string == 'Yes' else False
            logger.info('shortable: %s' % soup.b.string)
        elif 'Market Cap' in line:
            soup = BeautifulSoup(line, 'html.parser')
            market_cap = soup.b.string

            if market_cap[-1] == 'B':
                billion = float(market_cap[:-1])
                if billion >= 200:
                    underlying.market_cap = 'mega'
                elif 10 <= billion < 200:
                    underlying.market_cap = 'large'
                elif 2 <= billion < 10:
                    underlying.market_cap = 'mid'
                else:
                    underlying.market_cap = 'small'
            elif market_cap[-1] == 'M':
                million = float(market_cap[:-1])
                if million >= 300:
                    underlying.market_cap = 'small'
                elif 50 <= million < 300:
                    underlying.market_cap = 'micro'
                else:
                    underlying.market_cap = 'nano'

            logger.info('market cap: %s, %s' % (market_cap, underlying.market_cap))

        elif symbol_tag in line:
            # symbol found
            soup = BeautifulSoup(line, 'html.parser')
            exchange = soup.span.string[1:-1]

            soup = BeautifulSoup(html[i + 1], 'html.parser')
            try:
                company = soup.b.string
            except AttributeError:
                company = soup.td.string

            soup = BeautifulSoup(html[i + 2], 'html.parser')
            sector, industry, country = [l.string for l in soup.find_all('a')]

            logger.info('company: %s' % company)
            logger.info('exchange: %s' % exchange)
            logger.info('sector: %s' % sector)
            logger.info('industry: %s' % industry)
            logger.info('country: %s' % country)

            underlying.company = company
            underlying.exchange = exchange
            underlying.sector = sector
            underlying.industry = industry
            underlying.country = country

    logger.info('Save underlying')
    underlying.save()

    return redirect(reverse('admin:data_underlying_change', args=(underlying.id,)))


def add_split_history(request, symbol):
    """
    Download split history from website then add each of them into db
    :param request: request
    :param symbol: str
    :return: render
    """
    symbol = symbol.upper()

    url = 'http://getsplithistory.com/%s' % symbol
    logger.info('start download: %s' % url)

    try:
        req = urllib2.Request(url=url)
        f = urllib2.urlopen(req)
    except urllib2.HTTPError:
        return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))

    html = [unicode(l, 'utf-8') for l in f.readlines()]
    logger.info('done download html, data length: %d' % len(html))
    try:
        line = '%s' % [l for l in html if 'table-splits' in l].pop()
    except IndexError:
        line = ''
    soup = BeautifulSoup(line, 'html.parser')

    history = []
    table_cell = soup.find_all('td')
    for i, td in enumerate(table_cell):
        value = td.string

        if value is not None:
            try:
                date = pd.to_datetime(value).strftime('%Y-%m-%d')

                fraction = ''.join([t.string for t in table_cell[i + 1].contents])
                fraction = fraction.replace(' : ', '/')
                logger.info('date: %s, fraction: %s' % (date, fraction))

                split_history = SplitHistory(
                    symbol=symbol.upper(),
                    date=date,
                    fraction=fraction
                )
                history.append(split_history)

            except ValueError:
                pass

    if len(history):
        SplitHistory.objects.bulk_create(history)

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))


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
            path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
            logger.info('Remove path: %s' % path)

            os.remove(path)

            # update underlying
            underlying = Underlying.objects.get(symbol=symbol)
            underlying.optionable = False
            underlying.final = False
            underlying.enable = False
            underlying.missing = ''
            underlying.log = ''
            underlying.save()

            # reshape db
            # reshape_h5('quote.h5')

            return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))
    else:
        form = TruncateSymbolForm(
            initial={
                'symbol': symbol
            }
        )

        path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
        db = pd.HDFStore(path)
        names = ['thinkback', 'google', 'yahoo', 'earning', 'dividend', 'contract', 'option']
        keys = [
            'stock/thinkback', 'stock/google', 'stock/yahoo', 'event/earning', 'event/dividend',
            'option/final/contract', 'option/final/data'
        ]

        df = {}
        for name, key in zip(names, keys):
            try:
                df[name] = db.select(key)
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


def manage_underlying(request, symbol):
    """
    All underlying management goes here
    :param request: request
    :param symbol: str
    :return: render
    """
    underlying = Underlying.objects.get(
        Q(symbol=symbol.upper()) | Q(symbol=symbol.lower())
    )
    split_history = SplitHistory.objects.filter(symbol=symbol.upper())
    split_history = '\n'.join('%s | %s | %s' % (s.symbol, s.date, s.fraction) for s in split_history)

    template = 'data/manage_underlying.html'
    parameters = dict(
        site_title='Manage underlying',
        title='Manage underlying: %s' % symbol.upper(),
        symbol=symbol,
        underlying=underlying,
        split_history=split_history
    )

    return render(request, template, parameters)
