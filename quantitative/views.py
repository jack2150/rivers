from bootstrap3_datetime.widgets import DateTimePicker
import datetime
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Q
from django.shortcuts import render, redirect
from django import forms
from pandas.tseries.offsets import BDay
from data.models import Stock, Underlying
from quantitative.models import *


# noinspection PyArgumentList
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

    algorithm_id = forms.IntegerField(widget=forms.HiddenInput())

    algorithm_rule = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))

    algorithm_formula = forms.CharField(widget=forms.TextInput(
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
                    choices=[(key, value.upper()) for key, value in zip(default, default)]
                )
            else:
                # text input
                self.fields[arg] = forms.CharField(
                    label=arg.capitalize(),
                    widget=forms.TextInput(attrs={
                        'class': 'form-control vTextField',
                        'required': 'required'
                    }),
                    help_text='Sample: 20:100:10',
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
                        Stock.objects.get(symbol=symbol)
                    except MultipleObjectsReturned:
                        pass
                    except ObjectDoesNotExist:
                        symbol_errors.append('Symbol <{symbol}> not found.'.format(
                            symbol=symbol
                        ))
                else:
                    if symbol_errors:
                        self._errors['symbol'] = self.error_class(symbol_errors)

        # valid algorithm id
        arguments = list()
        algorithm_id = cleaned_data.get('algorithm_id')
        try:
            algorithm = Algorithm.objects.get(id=algorithm_id)
            arguments = algorithm.get_args()
        except ObjectDoesNotExist:
            self._errors['algorithm_id'] = self.error_class(
                ['Algorithm id {algorithm_id} is not found.'.format(
                    algorithm_id=algorithm_id
                )]
            )

        for arg, default in arguments:
            try:
                # note: select field already have choices validation
                data = cleaned_data[arg]

                if type(default) == tuple:
                    if data not in default:
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
        Using generate variables and run algorithm
        :return: AlgorithmResult
        """

        # prepare symbols
        symbols = self.cleaned_data['symbol'].upper()
        if ',' not in symbols:
            # single
            if symbols == 'ALL':
                # special case, all symbols, postgre support distinct
                symbols = [s[0] for s in Stock.objects.distinct('symbol').values_list('symbol')
                           if s[0] != 'SPY']
            else:
                symbols = [symbols]

        elif ',' in symbols:
            # multi symbol
            symbols = [s.replace(' ', '') for s in symbols.split(',')]

        # prepare values and algorithm
        algorithm = Algorithm.objects.get(id=self.cleaned_data['algorithm_id'])
        algorithm.quant.set_args({
            key: value for key, value in self.cleaned_data.items()
            if 'algorithm_' not in key and key not in ('symbol', 'start_date', 'stop_date')
        })

        algorithm.quant.set_date(
            start=self.cleaned_data['start_date'],
            stop=self.cleaned_data['stop_date'],
        )
        algorithm.quant.seed_data(symbols)
        reports = algorithm.quant.make_reports()

        if reports.count():
            algorithm_results = list()
            for report in reports:
                algorithm_results.append(AlgorithmResult(**report))
            else:
                return AlgorithmResult.objects.bulk_create(algorithm_results)


def algorithm_analysis(request, algorithm_id, argument_id=0):
    """
    View that use for testing algorithm then generate analysis report
    :param request: request
    :param algorithm_id: int
    :return: render
    """
    algorithm = Algorithm.objects.get(id=algorithm_id)

    # extract arguments
    arguments = algorithm.get_args()

    if request.method == 'POST':
        form = AlgorithmAnalysisForm(request.POST, arguments=arguments)
        if form.is_valid():
            form.analysis()
            return redirect('admin:quantitative_algorithmresult_changelist')
    else:
        initial = {
            'algorithm_id': algorithm.id,
            'algorithm_rule': algorithm.rule,
            'algorithm_formula': algorithm.formula,
            'start_date': datetime.date(year=2009, month=1, day=1),
            'stop_date': datetime.date(
                year=datetime.datetime.today().year,
                month=datetime.datetime.today().month,
                day=1) - BDay(1),
        }

        if int(argument_id):
            algorithm_argument = AlgorithmArgument.objects.get(
                Q(id=argument_id) & Q(algorithm=algorithm)
            )
            args = algorithm_argument.get_args()
            initial.update(args)

        form = AlgorithmAnalysisForm(
            arguments=arguments,
            initial=initial
        )

    template = 'quant/algorithm/analysis.html'

    parameters = dict(
        site_title='Algorithm Analysis',
        title='Algorithm Analysis',
        form=form,
        arguments=arguments,
        underlyings=Underlying.objects.all()
    )

    return render(request, template, parameters)
