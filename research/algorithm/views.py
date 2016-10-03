import datetime
import logging
import pandas as pd
import os
from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from pandas.tseries.offsets import BDay

from base.ufunc import latest_season, ts
from data.models import Underlying
from research.algorithm.models import Formula, FormulaArgument, FormulaResult
from rivers.settings import BASE_DIR, RESEARCH_DIR

logger = logging.getLogger('views')


class AlgorithmAnalysisForm(forms.Form):
    symbol = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control vTextField',
            'required': 'required',
            'style': 'text-transform:uppercase'
        }),
        help_text='Sample: ALL, "SPY,AIG", SP500...'
    )

    start_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )
    stop_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )

    formula_id = forms.IntegerField(widget=forms.HiddenInput())

    formula_rule = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))

    def __init__(self, *args, **kwargs):
        arguments = kwargs.pop('arguments')
        super(AlgorithmAnalysisForm, self).__init__(*args, **kwargs)

        for arg, default in arguments:
            if type(default) == tuple:
                # choice field
                self.fields[arg] = forms.ChoiceField(
                    label=arg.capitalize(),
                    widget=forms.Select(attrs={
                        'class': 'form-control vTextField',
                        'required': 'required'
                    }),
                    choices=[('all', 'ALL')] +
                            [(key, value.upper()) for key, value in zip(default, default)]
                )
            else:
                # text input
                self.fields[arg] = forms.CharField(
                    label=arg.capitalize(),
                    widget=forms.TextInput(attrs={
                        'class': 'form-control vTextField',
                        'required': 'required'
                    }),
                    help_text='(20:100:10, 20:30, 20)',
                )

    def clean(self):
        """
        Validate input data from ready algorithm form
        """
        cleaned_data = super(AlgorithmAnalysisForm, self).clean()

        # check symbol exists
        # special case like sp500 all symbols not yet include
        symbol = cleaned_data.get('symbol').upper()
        if symbol is not None:
            if symbol == 'ALL':
                pass
            else:
                if ',' in symbol:
                    # multiple symbols
                    symbols = [s.replace(' ', '') for s in symbol.split(',')]
                else:
                    # single symbol
                    symbols = [symbol]

                symbol_errors = list()
                for symbol in symbols:
                    try:
                        underlying = Underlying.objects.get(symbol=symbol.upper())

                        if not underlying.enable:
                            symbol_errors.append('Symbol <{symbol}> not enable for test.'.format(
                                symbol=symbol
                            ))

                    except ObjectDoesNotExist:
                        symbol_errors.append('Symbol <{symbol}> underlying not found.'.format(
                            symbol=symbol
                        ))
                else:
                    if symbol_errors:
                        self._errors['symbol'] = self.error_class(symbol_errors)

        # valid algorithm id
        arguments = list()
        formula_id = cleaned_data.get('formula_id')
        try:
            algorithm = Formula.objects.get(id=formula_id)
            arguments = algorithm.get_args()

        except ObjectDoesNotExist:
            self._errors['formula_id'] = self.error_class(
                ['Formula id {formula_id} is not found.'.format(
                    formula_id=formula_id
                )]
            )

        for arg, default in arguments:
            try:
                # note: select field already have choices validation
                data = cleaned_data[arg]

                if type(default) == tuple:
                    if data not in default and data != 'all':
                        self._errors[arg] = self.error_class(
                            ['{arg} invalid choices.'.format(arg=arg.capitalize())]
                        )
                else:
                    if ':' in data:
                        [float(d) for d in data.split(':')]
                    elif float(data) < 0:
                        self._errors[arg] = self.error_class(
                            ['{arg} value can only be positive.'.format(
                                arg=arg.capitalize()
                            )]
                        )
            except KeyError:
                self._errors[arg] = self.error_class(
                    ['KeyError {arg} field value.'.format(arg=arg.capitalize())]
                )
            except ValueError:
                self._errors[arg] = self.error_class(
                    ['ValueError {arg} field value.'.format(arg=arg.capitalize())]
                )

        return cleaned_data

    def analysis(self):
        """
        Using generate variables and run algorithm backtest
        """
        # prepare values and formula
        fields = {
            key: value for key, value in self.cleaned_data.items()
            if 'formula_' not in key and key not in ('symbol', 'start_date', 'stop_date')
        }

        # save args
        formula = Formula.objects.get(id=self.cleaned_data['formula_id'])
        formula_args = FormulaArgument.objects.filter(Q(formula=formula) & Q(arguments=fields))
        if formula_args.exists() == 0:
            formula_arg = FormulaArgument(
                formula=formula,
                arguments=fields,
                level='low',
                result='undefined',
                description=''
            )
            formula_arg.save()

        logger.info('Start backtest algorithm')

        cmd = 'start cmd /k python %s algorithm --symbol=%s ' \
              '--formula_id=%d --start="%s" --stop="%s" --fields="%s"' % (
                  os.path.join(BASE_DIR, 'research', 'backtest.py'),
                  self.cleaned_data['symbol'],
                  self.cleaned_data['formula_id'],
                  self.cleaned_data['start_date'],
                  self.cleaned_data['stop_date'],
                  str(fields)
              )

        os.system(cmd)

        return redirect(reverse(
            'admin:manage_underlying', kwargs={'symbol': self.cleaned_data['symbol']}
        ))


def algorithm_analysis(request, formula_id, argument_id=0):
    """
    View that use for testing algorithm then generate analysis report
    :param request: request
    :param formula_id: int
    :param argument_id: int
    :return: render
    """
    formula = Formula.objects.get(id=formula_id)

    # extract arguments
    arguments = formula.get_args()

    if request.method == 'POST':
        form = AlgorithmAnalysisForm(request.POST, arguments=arguments)
        if form.is_valid():
            form.analysis()
            return redirect(reverse(
                'admin:algorithm_analysis', kwargs={
                    'formula_id': formula_id, 'argument_id': argument_id
                }
            ))
    else:
        season = latest_season()
        initial = {
            'formula_id': formula.id,
            'formula_rule': formula.rule,
            'formula_equation': formula.equation,
            'start_date': datetime.date(year=2010, month=1, day=1),
            'stop_date': datetime.date(
                year=season.year,
                month=season.month,
                day=season.day
            )
        }

        if int(argument_id):
            algorithm_argument = FormulaArgument.objects.get(
                Q(id=argument_id) & Q(formula=formula)
            )
            args = algorithm_argument.get_args()
            initial.update(args)

        form = AlgorithmAnalysisForm(
            arguments=arguments,
            initial=initial
        )

    template = 'algorithm/analysis.html'

    parameters = dict(
        site_title='Algorithm Analysis',
        title='Algorithm Analysis',
        form=form,
        arguments=arguments,
        underlyings=Underlying.objects.filter(enable=True)
    )

    return render(request, template, parameters)


def algorithm_signal_view(request, symbol, date, formula_id, report_id):
    """
    Algorithm df_signal view
    :param request: request
    :param symbol: str
    :param date: str
    :param formula_id: int
    :param report_id: int
    :return: render
    """
    formula = Formula.objects.get(id=formula_id)

    db = pd.HDFStore(os.path.join(RESEARCH_DIR, '%s.h5' % symbol.lower()))
    df_report = db.select('algorithm/report', where='date == %r & formula == %r' % (
        date, formula.path
    ))
    report = df_report.iloc[int(report_id)]
    """:type: pd.DataFrame"""
    df_signal = db.select(
        'algorithm/signal', where='formula == %r & date == %r & hd == %r & cs == %r' % (
            report['formula'], date, report['hd'], report['cs']
        )
    ).reset_index(drop=True)
    db.close()

    df_signal['pl_cumsum'] = df_signal['pct_chg'].cumsum()
    # noinspection PyUnresolvedReferences
    df_signal['pl_cumprod'] = (1 + df_signal['pct_chg']).cumprod() - 1
    first_date = int(df_signal['date0'].iloc[0].value // 10 ** 6)

    signals = []
    for index, data in df_signal.iterrows():
        signal = {
            'index': index,
            'date_index': int(data['date1'].value // 10 ** 6),
            'date0': str(data['date0'].date()),
            'date1': str(data['date1'].date()),
            'holding': data['holding'].days,
            'signal0': data['signal0'],
            'signal1': data['signal1'],
            'close0': data['close0'],
            'close1': data['close1'],
            'pct_chg': round(data['pct_chg'] * 100, 2),
            'pl_cumsum': round(data['pl_cumsum'], 2),
            'pl_cumprod': round(data['pl_cumprod'], 2),
        }
        signals.append(signal)

    report = {
        'start': str(report['start'].date()),
        'stop': str(report['stop'].date()),
        'sharpe_rf': round(report['sharpe_rf'] * 100, 4),
        'sharpe_spy': round(report['sharpe_spy'] * 100, 4),
        'sortino_rf': round(report['sortino_rf'] * 100, 4),
        'sortino_spy': round(report['sortino_spy'] * 100, 4),
        'buy_hold': round(report['buy_hold'], 4),
        'pl_count': report['pl_count'],
        'pl_sum': round(report['pl_sum'], 4),
        'pl_cumprod': round(report['pl_cumprod'], 4),
        'pl_mean': round(report['pl_mean'], 4),
        'pl_std': round(report['pl_std'], 4),
        'profit_chance': round(report['profit_chance'], 2),
        'loss_chance': round(report['loss_chance'], 2),
        'handle_data': report['hd'],
        'create_signal': report['cs'],
    }

    template = 'algorithm/signal.html'
    parameters = dict(
        site_title='Algorithm Signal',
        title='Signal: < %s > %s' % (symbol.upper(), formula),
        symbol=symbol,
        signals=signals,
        first_date=first_date,
        report=report
    )

    return render(request, template, parameters)


def algorithm_trade_view(request, symbol, date, formula_id, report_id):
    """
    Algorithm df_list view for each trade in df_signal
    :param request: request
    :param symbol: str
    :param date: str
    :param formula_id: int
    :param report_id: int
    :return: render
    """
    formula = Formula.objects.get(id=formula_id)

    db = pd.HDFStore(os.path.join(RESEARCH_DIR, '%s.h5' % symbol.lower()))
    df_report = db.select('algorithm/report', where='date == %r & formula == %r' % (
        date, formula.path
    ))
    report = df_report.iloc[int(report_id)]
    """:type: pd.DataFrame"""
    df_signal = db.select(
        'algorithm/signal', where='formula == %r & date == %r & hd == %r & cs == %r' % (
            report['formula'], date, report['hd'], report['cs']
        )
    ).reset_index(drop=True)
    db.close()

    signals = []
    for index, data in df_signal.iterrows():
        signal = {
            'index': index,
            'date0': str(data['date0'].date()),
            'date1': str(data['date1'].date()),
            'signal0': data['signal0'],
            'signal1': data['signal1'],
            'close0': data['close0'],
            'close1': data['close1'],
            'pct_chg': round(data['pct_chg'] * 100, 2),
            'holding': data['holding'].days
        }

        signals.append(signal)

    # generate df_list for display
    formula.backtest.set_symbol_date(symbol)
    formula.backtest.convert_data()
    formula.backtest.set_signal(df_signal)
    formula.backtest.prepare_join()

    df_list = formula.backtest.df_list

    # keys = ['open', 'high', 'low', 'close', 'volume', 'chg0']
    trades = []
    for df in df_list:
        trade = []
        for index, data in df.iterrows():
            stock = {
                'index0': int(index.value // 10 ** 6),
                'index1': str(index.date()),
                'open': round(data['open'], 2),
                'high': round(data['high'], 2),
                'low': round(data['low'], 2),
                'close': round(data['close'], 2),
                'volume': int(data['volume']),
                'pct_chg': round(data['chg0'] * 100, 2),
            }

            trade.append(stock)

        trades.append(trade)

    template = 'algorithm/trade.html'

    parameters = dict(
        site_title='Algorithm Trade View',
        title='Trade: < %s > %s' % (
            symbol.upper(), formula
        ),
        symbol=symbol,
        formula_id=formula.id,
        trades=trades,
        signals=signals,
        handle_data=report['hd'],
        create_signal=report['cs']
    )

    return render(request, template, parameters)


def algorithm_report_view(request, symbol, date, formula_id):
    """
    Algorithm research report view
    :param request: request
    :param symbol: str
    :param date: str
    :param formula_id: int
    :return: render
    """
    formula = Formula.objects.get(id=formula_id)
    db = pd.HDFStore(os.path.join(RESEARCH_DIR, '%s.h5' % symbol.lower()))
    df_report = db.select('algorithm/report', where='date == %r & formula == %r' % (
        date, formula.path
    ))
    """:type: pd.DataFrame"""
    db.close()

    df_report, args, _, _ = remake_report(formula, df_report)

    template = 'algorithm/report.html'
    parameters = dict(
        site_title='Formula Report',
        title='Symbol: < %s > Formula: %s' % (symbol.upper(), formula),
        symbol=symbol,
        formula_id=formula_id,
        date=date,
        args=args,
        keys=list(df_report.columns),
        length=len(df_report.columns)
    )

    return render(request, template, parameters)


@csrf_exempt
def algorithm_report_json(request, symbol, date, formula_id):
    """
    output report data into json format using datatable query
    :param request: request
    :param symbol: str
    :param date: str
    :param formula_id: int
    :return: HttpResponse
    """
    draw = int(request.GET.get('draw'))
    order_column = int(request.GET.get('order[0][column]'))
    order_dir = request.GET.get('order[0][dir]')
    logger.info('order column: %s, dir: %s' % (order_column, order_dir))

    start = int(request.GET.get('start'))
    length = int(request.GET.get('length'))
    logger.info('start: %d length: %d' % (start, length))

    formula = Formula.objects.get(id=formula_id)

    db = pd.HDFStore(os.path.join(RESEARCH_DIR, '%s.h5' % symbol.lower()))
    df_report = db.select('algorithm/report', where='date == %r & formula == %r' % (
        date, formula.path
    ))
    """:type: pd.DataFrame"""
    db.close()

    df_report, args, hd_args, cs_args = remake_report(formula, df_report)

    keys = list(df_report.columns)

    # server side
    df_page = df_report

    if keys[order_column] != 'date':
        df_page = df_page.sort_values(
            keys[order_column], ascending=True if order_dir == 'asc' else False
        )
    df_page = df_page[start:start + length]

    reports = []
    for index, data in df_page.iterrows():
        temp = []

        for key in keys:
            if 'hd_' in key or 'cs_' in key:
                try:
                    if int(data[key]) == float(data[key]):
                        temp.append(int(data[key]))
                    else:
                        temp.append(float(data[key]))
                except ValueError:
                    temp.append('"%s"' % str(data[key]))

            elif key in ('date', 'start', 'stop'):
                temp.append('"%s"' % str(data[key].date()))
            elif key == 'formula':
                pass
            else:
                temp.append(round(data[key], 4))

        temp.append('"%s,%s"' % (reverse('admin:algorithm_signal_view', kwargs={
            'symbol': symbol.lower(),
            'date': date,
            'formula_id': formula.id,
            'report_id': index,
        }), reverse('admin:algorithm_signal_raw', kwargs={
            'symbol': symbol.lower(),
            'date': date,
            'formula_id': formula.id,
            'report_id': index,
        })))

        temp.append('"%s"' % reverse('admin:algorithm_trade_view', kwargs={
            'symbol': symbol.lower(),
            'date': date,
            'formula_id': formula.id,
            'report_id': index,
        }))
        temp.append('"%s"' % reverse('admin:strategy_analysis1', kwargs={
            'symbol': symbol.lower(),
            'date': date,
            'formula_id': formula.id,
            'report_id': index,
        }))

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
        draw,
        len(df_report),
        len(df_report),
        ',\n\t\t\t'.join(reports)
    )

    return HttpResponse(data, content_type="application/json")


def algorithm_signal_raw(request, symbol, date, formula_id, report_id):
    """
    Raw algorithm trade view with fix columns
    :param request: request
    :param symbol: str
    :param date:
    :param formula_id: int
    :param report_id: int
    :return: render
    """
    formula = Formula.objects.get(id=formula_id)

    db = pd.HDFStore(os.path.join(RESEARCH_DIR, '%s.h5' % symbol.lower()))
    df_report = db.select(
        'algorithm/report', where='formula == %r & date == %r' % (formula.path, date)
    )
    """:type: pd.DataFrame"""
    report = df_report.ix[int(report_id)]
    df_signal = db.select(
        'algorithm/signal', where='formula == %r & date == %r & hd == %r & cs == %r' % (
            formula.path, date, report['hd'], report['cs']
        )
    )
    db.close()

    template = 'base/raw_df.html'
    parameters = dict(
        site_title='Algorithm Trade',
        title='Formula: < %s > %s' % (symbol.upper(), formula),
        symbol=symbol,
        data=df_signal.to_string(line_width=1000),
        trade=formula,
        args='<handle_data|%s> <create_signal|%s>' % (report['hd'], report['cs']),
    )

    return render(request, template, parameters)


@csrf_exempt
def algorithm_report_chart(request, symbol, date, formula_id):
    """
    Algorithm report chart by bdays
    :param request: request
    :param symbol: str
    :param date: str
    :param formula_id: int
    :return: render
    """
    formula = Formula.objects.get(id=formula_id)

    db = pd.HDFStore(os.path.join(RESEARCH_DIR, '%s.h5' % symbol.lower()))
    df_report = db.select('algorithm/report', where='date == %r & formula == %r' % (
        date, formula.path
    ))
    """:type: pd.DataFrame"""
    db.close()

    # start
    df_report, args, hd_args, cs_args = remake_report(formula, df_report)

    # set default parameters
    if request.method != 'POST':
        first = df_report.iloc[0]
        values = {}
        for arg in hd_args:
            if 'bdays' not in arg:
                values['hd_%s' % arg] = first['hd_%s' % arg]

        for arg in cs_args:
            if 'bdays' not in arg:
                values['cs_%s' % arg] = first['cs_%s' % arg]
    else:
        values = {}
        for k, v in request.POST.items():
            try:
                if int(v) == float(v):
                    values[k] = int(v)
                else:
                    values[k] = float(v)
            except ValueError:
                values[k] = str(v)

    logger.info('values: %s' % values)

    # query params
    df_page = df_report.copy()
    if len(values):
        query = ' & '.join(['%s == %r' % (k, v) for k, v in values.items()])

        df_page = df_report.query(query)
        # ts(df_page)

    # get bdays data
    if 'hd_bdays' in args:
        bdays = 'hd_bdays'
    elif 'cs_bdays' in args:
        bdays = 'cs_bdays'
    else:
        raise LookupError('No holding days research')

    # generate require data
    data = {
        'move_mean': ','.join([s for s in df_page.apply(
            lambda x: '[%d, %.2f]' % (int(x[bdays]), x['pl_mean']), axis=1
        )]),
        'max_range': ','.join(df_page.apply(
            lambda x: '[%d, %.2f, %.2f]' % (int(x[bdays]), x['profit_max'], x['loss_max']), axis=1
        ))
    }

    # put into list_str
    keys = (
        'profit_chance', 'pl_mean', 'sharpe_rf', 'sharpe_spy', 'sortino_rf', 'sortino_spy',
    )
    for key in keys:
        data[key] = list_str(df_page, key)

    # set parameter for other cs/hd
    fields = []
    for arg in args:
        if arg not in ('hd_bdays', 'cs_bdays'):
            fields.append((arg, values[arg], list(df_report[arg].unique())))

    template = 'algorithm/chart.html'
    parameters = dict(
        site_title='Algorithm Report Chart',
        title='Formula: < %s > %s' % (symbol.upper(), formula),
        symbol=symbol,
        bdays=','.join(['%d' % int(d) for d in df_page[bdays]]),
        data=data,
        fields=fields,
        link=reverse('admin:algorithm_report_chart', kwargs={
            'symbol': symbol,
            'date': date,
            'formula_id': formula_id
        })
    )

    return render(request, template, parameters)


def list_str(df_report, key):
    """
    Join float list into str
    :param df_report: pd.DataFrame
    :param key: str
    :return: str
    """
    return ','.join(['%.2f' % (d * 100) for d in df_report[key]])


def remake_report(formula, df_report):
    """
    Remake df_report with hd/cs columns
    :param formula: Formula
    :param df_report: pd.DataFrame
    :return: pd.DataFrame
    """
    df_report = df_report.sort_index()
    args = formula.get_args()
    dtypes = {}
    for key, arg in args:
        try:
            int(arg)
            dtypes[key] = int
        except TypeError:
            dtypes[key] = str

    hd_args = sorted([a[0][len('handle_data_'):] for a in args if 'handle_data' in a[0]])
    cs_args = sorted([a[0][len('create_signal_'):] for a in args if 'create_signal' in a[0]])
    # print hd_args
    # print cs_args
    for i, arg in enumerate(hd_args, 0):
        df_report['hd_%s' % arg] = df_report['hd'].apply(
            lambda x: x.split(',')[i]
        ).astype(dtypes['handle_data_%s' % arg])

    for i, arg in enumerate(cs_args, 0):
        df_report['cs_%s' % arg] = df_report['cs'].apply(
            lambda x: x.split(',')[i]
        ).astype(dtypes['create_signal_%s' % arg])

    # remove hd, cs
    del df_report['hd'], df_report['cs']

    # reorder columns
    columns = list(df_report.columns)
    args = columns[31:]
    columns = columns[:2] + columns[31:] + columns[2:31]
    df_report = df_report[columns]
    del df_report['formula']

    return df_report, args, hd_args, cs_args
