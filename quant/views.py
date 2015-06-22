from importlib import import_module
from inspect import getargspec
import os
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.shortcuts import render, redirect
from django import forms
from itertools import product
import pandas as pd
import numpy as np
from data.models import Stock
from quant.analysis import Quant
from quant.models import Algorithm, AlgorithmResult
from rivers.settings import BASE_DIR


# noinspection PyArgumentList
class AlgorithmAnalysisForm(forms.Form):
    symbol = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control vTextField',
            'required': 'required'
        }),
        help_text='"ALL", "SPY,AIG", "SP500"...'
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
            arg = arg

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

    def generate_values(self):
        """
        Generate a list of variables
        :rtype : dict of list
        """
        values = dict()
        arguments = [key for key in self.cleaned_data.keys()
                     if 'algorithm_' not in key and key is not 'symbol']

        for arg in arguments:
            if ':' in self.cleaned_data[arg]:
                data = [int(i) for i in self.cleaned_data[arg].split(':')]
                try:
                    start, stop, step = [int(i) for i in data]
                except ValueError:
                    start, stop = [int(i) for i in data]
                    step = 1

                values[arg] = np.arange(start, stop + 1, step)
            else:
                try:
                    values[arg] = [int(self.cleaned_data[arg])]
                except ValueError:
                    raise ValueError('Unable convert {arg} into int'.format(arg=arg))

        # make it a list
        keys = sorted(values.keys())
        t = list()
        for key in keys:
            t.append(['%s=%s' % (key, v) for v in values[key]])

        # support multiple variables once
        line = 'dict(%s)' % ','.join(['%s'] * len(t))
        values = [eval(line % x) for x in list(product(*t))]

        return values

    def run_algorithm_test(self):
        """
        Using generate variables and run algorithm
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
            symbols = symbols.split(',')

        # prepare values and algorithm
        values = self.generate_values()
        algorithm = Algorithm.objects.get(id=self.cleaned_data['algorithm_id'])

        # import function
        path = 'quant.algorithm.{path}'.format(path=algorithm.path)

        module = import_module(path)
        handle_data = getattr(module, 'handle_data')
        create_signal = getattr(module, 'create_signal')

        # get signal
        hd_keys = [a for a in getargspec(handle_data).args if a not in ('self', 'df')]
        cs_keys = [a for a in getargspec(create_signal).args if a not in ('self', 'df')]

        results = list()
        for symbol in symbols:
            for value in values:
                value = value
                """:type: dict"""

                # set method into quant model
                quant = Quant()
                quant.handle_data = handle_data
                quant.create_signal = create_signal
                quant.seed_data(symbol)

                df_stock = quant.handle_data(
                    quant.data[symbol],
                    **{key: value for key, value in value.items() if key in hd_keys}
                )
                df_signal = quant.create_signal(
                    df_stock,
                    **{key: value for key, value in value.items() if key in cs_keys}
                )

                # make report
                report = quant.report(df_stock, df_signal)
                report['symbol'] = symbol
                report['date'] = pd.datetime.today().date()
                report['algorithm'] = algorithm
                report['arguments'] = value.__str__()
                report['signals'] = df_signal.to_csv()

                # add into report
                result = AlgorithmResult(**report)
                results.append(result)

        if results:
            AlgorithmResult.objects.bulk_create(results)


def algorithm_analysis(request, algorithm_id):
    """
    View that use for testing algorithm then generate analysis report
    :param request: request
    :param algorithm_id: int
    :return: render
    """
    if id:
        algorithm = Algorithm.objects.get(id=algorithm_id)

        # import function
        handle_data, create_signal = algorithm.get_module()

        # extract arguments
        arguments = getargspec(handle_data).args + getargspec(create_signal).args
        arguments = [v for v in arguments if v not in ('self', 'df')]

        if request.method == 'POST':
            form = AlgorithmAnalysisForm(request.POST, arguments=arguments)
            if form.is_valid():
                form.run_algorithm_test()
                return redirect('admin:quant_algorithmresult_changelist')
        else:
            form = AlgorithmAnalysisForm(
                arguments=arguments,
                initial={
                    'algorithm_id': algorithm.id,
                    'algorithm_rule': algorithm.rule,
                    'algorithm_formula': algorithm.formula,
                }
            )
    else:
        raise LookupError('Algorithm not found.')

    template = 'quant/algorithm/ready.html'

    parameters = dict(
        site_title='Algorithm Analysis',
        title='Algorithm Analysis',
        form=form,
        arguments=arguments,
    )

    return render(request, template, parameters)
