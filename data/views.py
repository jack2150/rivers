from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from data.models import Underlying
from rivers.settings import QUOTE
import pandas as pd


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
                'event/earning/%s', 'event/dividend/%s',
                'option/%s/raw/contract', 'option/%s/raw/data',
                'option/%s/clean/contract', 'option/%s/clean/data',
                'option/%s/other/contract', 'option/%s/other/data',
                'option/%s/final/contract', 'option/%s/final/data',
            ]
            for key in keys:
                try:
                    db.remove(key % symbol.lower())
                except KeyError:
                    pass

            db.close()

            # update underlying
            underlying = Underlying.objects.get(symbol=symbol)
            underlying.option = False
            underlying.final = False
            underlying.missing = ''
            underlying.log = ''
            underlying.save()

            return redirect(reverse('admin:data_underlying_changelist'))
    else:
        form = TruncateSymbolForm(
            initial={'symbol': symbol}
        )

        db = pd.HDFStore(QUOTE)

        names = ['thinkback', 'google', 'yahoo', 'contract', 'option', 'earning', 'dividend']
        keys = [
            'stock/thinkback/%s', 'stock/google/%s', 'stock/yahoo/%s',
            'event/earning/%s', 'event/dividend/%s',
            'option/%s/raw/contract', 'option/%s/raw/data',
            'option/%s/clean/contract', 'option/%s/clean/data',
            'option/%s/other/contract', 'option/%s/other/data',
            'option/%s/final/contract', 'option/%s/final/data'
        ]

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

# todo: rework truncate


def manage_underlying(request, symbol):
    """
    All underlying management goes here
    :param request: request
    :param symbol: str
    :return: render
    """
    underlying = Underlying.objects.get(symbol=symbol.upper())

    template = 'data/manage_underlying.html'
    parameters = dict(
        site_title='Manage underlying',
        title='Manage underlying: %s' % symbol.upper(),
        symbol=symbol,
        underlying=underlying
    )

    return render(request, template, parameters)
