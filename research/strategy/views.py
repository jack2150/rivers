# noinspection PyUnusedLocal
import os

import pandas as pd
from django import forms
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from research.algorithm.models import Formula
from research.strategy.models import Trade, Commission
from rivers.settings import RESEARCH, BASE_DIR


class StrategyAnalysisForm1(forms.Form):
    formula_id = forms.IntegerField(widget=forms.HiddenInput())
    report_id = forms.IntegerField(widget=forms.HiddenInput())
    symbol = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))
    capital = forms.FloatField(
        widget=forms.NumberInput(
            attrs={'class': 'form-control vTextField'}
        )
    )
    trade = forms.ChoiceField(
        widget=forms.Select(
            attrs={'class': 'form-control vTextField'}
        )
    )
    commission = forms.ChoiceField(
        widget=forms.Select(
            attrs={'class': 'form-control vTextField'}
        )
    )

    def __init__(self, *args, **kwargs):
        super(StrategyAnalysisForm1, self).__init__(*args, **kwargs)

        trades = Trade.objects.order_by('id').values_list('id', 'name')
        self.fields['trade'].choices = trades

        commissions = [(c.id, c.__unicode__()) for c in Commission.objects.order_by('id')]
        self.fields['commission'].choices = commissions


def strategy_analysis1(request, symbol, formula_id, report_id):
    """
    Strategy analysis for select trade, commission and capital
    :param request: request
    :param symbol: str
    :param formula_id: int
    :param report_id: int
    :return: render
    """
    symbol = symbol.lower()
    formula = Formula.objects.get(id=formula_id)
    db = pd.HDFStore(os.path.join(RESEARCH, symbol, 'algorithm.h5'))
    report = db.select('report', where='formula == %r & index == %r' % (
        formula.path, report_id
    )).iloc[0]
    db.close()

    if request.method == 'POST':
        form = StrategyAnalysisForm1(request.POST)

        if form.is_valid():
            return redirect(reverse('admin:strategy_analysis2', kwargs={
                'symbol': symbol,
                'formula_id': formula_id,
                'report_id': report_id,
                'trade_id': form.cleaned_data['trade'],
                'commission_id': form.cleaned_data['commission'],
                'capital': int(form.cleaned_data['capital'])
            }))
    else:
        form = StrategyAnalysisForm1(initial={
            'formula_id': formula.id,
            'report_id': report_id,
            'symbol': symbol.upper(),
            'capital': 5000
        })

    template = 'strategy/analysis1.html'

    parameters = dict(
        site_title='Strategy analysis',
        title='Strategy analysis - select trade',
        form=form,
        report=dict(report),
        formula=formula
    )

    return render(request, template, parameters)


class StrategyAnalysisForm2(forms.Form):
    def __init__(self, *args, **kwargs):
        arguments = kwargs.pop('arguments')
        super(StrategyAnalysisForm2, self).__init__(*args, **kwargs)

        for arg, default in arguments:
            # print arg, zip(value, value)
            if type(default) == tuple:
                if all([type(d) == bool for d in default]):
                    choices = [(
                        ','.join([key for key in default]), 'BOTH'
                    )]
                    choices += [(int(key), str(value).upper()) for key, value in zip(default, default)]
                else:
                    choices = [(
                        ','.join([key for key in default]), 'ALL'
                    )]
                    choices += [(key, value.upper()) for key, value in zip(default, default)]

                # choice field
                self.fields[arg] = forms.ChoiceField(
                    label=arg.capitalize(),
                    widget=forms.Select(attrs={
                        'class': 'form-control vTextField',
                        'required': 'required'
                    }),
                    choices=choices
                )
            else:
                # text input
                self.fields[arg] = forms.CharField(
                    label=arg.capitalize(),
                    widget=forms.TextInput(attrs={
                        'class': 'form-control vTextField',
                        'required': 'required',
                    }),
                    help_text='Sample: 20:100:10',
                    initial=default
                )

    def analysis(self, **kwargs):
        """
        Backtest trade with arguments
        :param kwargs: dict
        """
        cmd = 'start cmd /k python %s strategy --symbol=%s ' \
              '--formula_id=%d --report_id=%d --trade_id=%d ' \
              '--commission_id=%d --capital=%d --fields="%s"' % (
                  os.path.join(BASE_DIR, 'research', 'backtest.py'),
                  kwargs['symbol'],
                  int(kwargs['formula_id']),
                  int(kwargs['report_id']),
                  int(kwargs['trade_id']),
                  int(kwargs['commission_id']),
                  int(kwargs['capital']),
                  str(self.cleaned_data)
              )

        os.system(cmd)

        return redirect(reverse(
            'admin:manage_underlying', kwargs={'symbol': kwargs['symbol']}
        ))


def strategy_analysis2(request, symbol, formula_id, report_id,
                       trade_id, commission_id, capital):
    """
    Strategy analysis for input arguments
    :param request: request
    :param symbol: str
    :param formula_id: int
    :param report_id: int
    :param trade_id: int
    :param commission_id: int
    :param capital: int
    :return: render
    """
    trade = Trade.objects.get(id=trade_id)
    commission = Commission.objects.get(id=commission_id)
    arguments = trade.get_args()

    if request.method == 'POST':
        form = StrategyAnalysisForm2(request.POST, arguments=arguments)

        if form.is_valid():
            form.analysis(**{
                'symbol': symbol,
                'formula_id': formula_id,
                'report_id': report_id,
                'trade_id': trade_id,
                'commission_id': commission_id,
                'capital': capital
            })
    else:
        form = StrategyAnalysisForm2(
            arguments=arguments
        )

    template = 'strategy/analysis2.html'

    parameters = dict(
        site_title='Strategy analysis',
        title='Strategy analysis - set arguments',
        form=form,
        trade=trade,
        commission=commission,
        capital=capital
    )

    return render(request, template, parameters)
