# noinspection PyUnusedLocal
import os
import logging
import pandas as pd
from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from base.ufunc import ts
from research.algorithm.models import Formula
from research.strategy.models import Trade, Commission
from rivers.settings import RESEARCH_DIR, BASE_DIR

logger = logging.getLogger('views')


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

        trades = Trade.objects.order_by('name').values_list('id', 'name')
        self.fields['trade'].choices = trades

        commissions = [(c.id, c.__unicode__()) for c in Commission.objects.order_by('id')]
        self.fields['commission'].choices = commissions


def strategy_analysis1(request, symbol, date, formula_id, report_id):
    """
    Strategy analysis for select trade, commission and capital
    :param request: request
    :param symbol: str
    :param date: str
    :param formula_id: int
    :param report_id: int
    :return: render
    """
    symbol = symbol.lower()
    formula = Formula.objects.get(id=formula_id)
    path = os.path.join(RESEARCH_DIR, '%s.h5' % symbol.lower())
    db = pd.HDFStore(path)
    report = db.select('algorithm/report', where='formula == %r & index == %r' % (
        formula.path, report_id
    )).iloc[0]
    db.close()

    if request.method == 'POST':
        form = StrategyAnalysisForm1(request.POST)

        if form.is_valid():
            return redirect(reverse('admin:strategy_analysis2', kwargs={
                'symbol': symbol,
                'date': date,
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
            'capital': 10000
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
                        ','.join([str(key) for key in default]), 'BOTH'
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
        cmd = 'start cmd /k python %s strategy --symbol=%s --date="%s" ' \
              '--formula_id=%d --report_id=%d --trade_id=%d ' \
              '--commission_id=%d --capital=%d --fields="%s"' % (
                  os.path.join(BASE_DIR, 'research', 'backtest.py'),
                  kwargs['symbol'],
                  kwargs['date'],
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


def strategy_analysis2(request, symbol, date, formula_id, report_id,
                       trade_id, commission_id, capital):
    """
    Strategy analysis for input arguments
    :param request: request
    :param symbol: str
    :param date: str
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
                'date': date,
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


def strategy_report_view(request, symbol, trade_id, date):
    """
    Algorithm research report view
    :param request: request
    :param symbol: str
    :param trade_id: int
    :param date: str
    :return: render
    """
    trade = Trade.objects.get(id=trade_id)

    template = 'strategy/report.html'

    parameters = dict(
        site_title='Strategy Report',
        title='Symbol: < %s > Strategy: %s' % (symbol.upper(), trade),
        symbol=symbol,
        trade_id=trade_id,
        date=date
    )

    return render(request, template, parameters)


@csrf_exempt
def strategy_report_json(request, symbol, trade_id, date):
    """
    output report data into json format using datatable query
    :param request: request
    :param symbol: str
    :param trade_id: int
    :param date: str
    :return: HttpResponse
    """
    draw = int(request.GET.get('draw'))
    order_column = int(request.GET.get('order[0][column]'))
    order_dir = request.GET.get('order[0][dir]')
    logger.info('order column: %s, dir: %s' % (order_column, order_dir))

    start = int(request.GET.get('start'))
    length = int(request.GET.get('length'))
    logger.info('start: %d length: %d' % (start, length))

    trade = Trade.objects.get(id=trade_id)

    db = pd.HDFStore(os.path.join(RESEARCH_DIR, '%s.h5' % symbol.lower()))
    df_report = db.select(
        'strategy/report',
        where='trade == %r & date == %r' % (trade.path, date)
    )
    """:type: pd.DataFrame"""
    db.close()

    keys = [
        'date', 'formula', 'report_id', 'args',
        'pl_count', 'pl_sum', 'pl_cumprod', 'pl_mean', 'pl_std',
        'profit_count', 'profit_chance', 'profit_max', 'profit_min',
        'loss_count', 'loss_chance', 'loss_max', 'loss_min',
        'dp_count', 'dp_chance', 'dp_mean', 'dl_count', 'dl_chance', 'dl_mean'
    ]

    # server side
    df_page = df_report[keys]
    df_page = df_page.sort_values(
        keys[order_column], ascending=True if order_dir == 'asc' else False
    )
    df_page = df_page[start:start + length]

    df_page['args'] = df_page['args'].apply(
        lambda x: x.replace('\'', '').replace('{', '').replace('}', '')
    )

    reports = []
    for index, data in df_page.iterrows():
        temp = []

        for key in keys:
            if key in ('args', 'formula', 'trade'):
                temp.append('"%s"' % data[key])
            elif key in ('date', 'start', 'stop'):
                temp.append('"%s"' % str(data[key].date()))
            else:
                temp.append(round(data[key], 4))

        temp.append('"%s"' % reverse('admin:strategy_order_raw', kwargs={
            'symbol': symbol.lower(),
            'trade_id': trade.id,
            'report_id': index,
        }))
        temp.append('"%s"' % reverse('admin:strategy_trade_raw', kwargs={
            'symbol': symbol.lower(),
            'trade_id': trade.id,
            'report_id': index,
        }))
        """
        temp.append('"%s"' % reverse('admin:strategy_analysis1', kwargs={
            'symbol': symbol.lower(),
            'formula_id': trade.id,
            'report_id': index,
        }))
        """

        reports.append(
            '[%s]' % ','.join(str(t) for t in temp)
        )

    data = """
    {
        "draw": %d,
        "recordsTotal": %d,
        "recordsFiltered": %d,
        "data": [
            %s
        ]
    }
    """ % (
        # draw,
        0,
        len(df_report),
        len(df_report),
        ',\n\t\t\t'.join(reports)
    )

    return HttpResponse(data, content_type="application/json")


def strategy_order_raw(request, symbol, trade_id, report_id):
    """
    Raw strategy order view with different columns
    :param request: request
    :param symbol: str
    :param trade_id: int
    :param report_id: int
    :return: render
    """
    trade = Trade.objects.get(id=trade_id)

    db = pd.HDFStore(os.path.join(RESEARCH_DIR, '%s.h5' % symbol.lower()))
    df_report = db.select('strategy/report', where='trade == %r' % trade.path)
    """:type: pd.DataFrame"""
    report = df_report.ix[int(report_id)]
    df_order = db.select(
        'strategy/order/%s' % trade.path.replace('.', '/'),
        where='trade == %r & args == %r' % (trade.path, report['args'])
    )
    db.close()

    template = 'base/raw_df.html'
    parameters = dict(
        site_title='Strategy Order',
        title='Order: < %s > %s' % (symbol.upper(), trade),
        symbol=symbol,
        data=df_order.to_string(line_width=1000),
        trade=trade,
        args=report['args']
    )

    return render(request, template, parameters)


def strategy_trade_raw(request, symbol, trade_id, report_id):
    """
    Raw strategy trade view with fix columns
    :param request: request
    :param symbol: str
    :param trade_id: int
    :param report_id: int
    :return: render
    """
    trade = Trade.objects.get(id=trade_id)

    db = pd.HDFStore(os.path.join(RESEARCH_DIR, '%s.h5' % symbol.lower()))
    df_report = db.select('strategy/report', where='trade == %r' % trade.path)
    """:type: pd.DataFrame"""
    report = df_report.ix[int(report_id)]
    df_trade = db.select(
        'strategy/trade',
        where='trade == %r & args == %r' % (trade.path, report['args'])
    )
    db.close()

    template = 'base/raw_df.html'
    parameters = dict(
        site_title='Strategy Trade',
        title='Trade: < %s > %s' % (symbol.upper(), trade),
        symbol=symbol,
        data=df_trade.to_string(line_width=1000),
        trade=trade,
        args=report['args']
    )

    return render(request, template, parameters)


# todo: real view, mini
















