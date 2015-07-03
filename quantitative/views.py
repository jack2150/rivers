from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Q
from django.shortcuts import render, redirect
from django import forms
from data.models import Stock
from quantitative.models import *


# noinspection PyArgumentList
class AlgorithmAnalysisForm(forms.Form):
    symbol = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control vTextField',
            'required': 'required'
        }),
        help_text='Sample: ALL, "SPY,AIG", SP500...'
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

        for arg in arguments:
            self.fields[arg] = forms.CharField(
                label=arg.capitalize(),
                widget=forms.TextInput(attrs={
                    'class': 'form-control vTextField',
                    'required': 'required'
                }),
                help_text='Sample: 20:100:10 ; Method: {name}'.format(
                    name=(
                        arg[:11] if 'handle_data' in arg else arg[:13]
                    ).replace('_', ' ').capitalize()
                ),
            )

    def clean(self):
        """
        Validate input data from ready algorithm form
        """
        cleaned_data = super(AlgorithmAnalysisForm, self).clean()

        # check symbol exists
        # special case like sp500 all symbols not yet include
        symbol = cleaned_data.get('symbol')
        if symbol is not None:
            if symbol.upper() == 'ALL':
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
        algorithm_id = cleaned_data.get('algorithm_id')
        try:
            Algorithm.objects.get(id=algorithm_id)
        except ObjectDoesNotExist:
            self._errors['algorithm_id'] = self.error_class(
                ['Algorithm id {algorithm_id} is not found.'.format(
                    algorithm_id=algorithm_id
                )]
            )

        # valid arguments
        arguments = {key: value for key, value in self.cleaned_data.items()
                     if 'algorithm_' not in key and key is not 'symbol'}

        for key, value in arguments.items():
            try:
                if ':' in value:
                    [int(v) for v in value.split(':')]
                else:
                    int(value)
            except ValueError:
                self._errors[key] = self.error_class(
                    ['{key} ({value}) is not valid.'.format(
                        key=key.capitalize(), value=value
                    )]
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
                print symbols
            else:
                symbols = [symbols]

        elif ',' in symbols:
            # multi symbol
            symbols = [s.replace(' ', '') for s in symbols.split(',')]

        # prepare values and algorithm
        algorithm = Algorithm.objects.get(id=self.cleaned_data['algorithm_id'])
        algorithm.quant.set_args({
            key: value for key, value in self.cleaned_data.items()
            if 'algorithm_' not in key and key is not 'symbol'
        })

        algorithm.quant.seed_data(symbols)
        reports = algorithm.quant.get_reports()

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
    hd_keys, cs_keys = algorithm.get_args()
    arguments = ['handle_data_%s' % k for k in hd_keys] + \
                ['create_signal_%s' % k for k in cs_keys]

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
    )

    return render(request, template, parameters)
