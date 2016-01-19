from StringIO import StringIO
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import render, redirect
from data.models import Underlying
from simulation.quant import StrategyQuant
from simulation.models import *


#get_strategy = lambda: Strategy.objects.values_list('id', 'name')


# noinspection PyUnusedLocal
class StrategyAnalysisForm1(forms.Form):
    algorithmresult_id = forms.IntegerField(widget=forms.HiddenInput())
    symbol = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))

    algorithm_id = forms.IntegerField(widget=forms.HiddenInput())
    algorithm_rule = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))
    algorithm_args = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))

    sharpe_ratio = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))
    probability = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))
    profit_loss = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))
    risk = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))

    strategy = forms.ChoiceField(
        widget=forms.Select(
            attrs={'class': 'form-control vTextField'}
        )
    )

    def __init__(self, *args, **kwargs):
        super(StrategyAnalysisForm1, self).__init__(*args, **kwargs)

        choices = Strategy.objects.order_by('id').reverse().values_list('id', 'name')
        self.fields['strategy'].choices = choices

    def clean(self):
        """
        Validate form data
        """
        cleaned_data = super(StrategyAnalysisForm1, self).clean()

        # check algorithm is exists
        try:
            algorithmresult_id = cleaned_data['algorithmresult_id']
            AlgorithmResult.objects.get(id=algorithmresult_id)
        except (ObjectDoesNotExist, KeyError) as e:
            self._errors['algorithmresult_id'] = self.error_class(
                ['Algorithm result id does not exists.']
            )

        # check strategy is exists
        try:
            strategy_id = cleaned_data['strategy']
            Strategy.objects.get(id=strategy_id)
        except (ObjectDoesNotExist, KeyError) as e:
            self._errors['strategy'] = self.error_class(
                ['Strategy does not exists.']
            )

        return cleaned_data


def strategy_analysis1(request, algorithmresult_id):
    """
    Simulation strategy 1 for select strategy
    :param request: request
    :param algorithmresult_id: int
    :return: render
    """
    template = 'simulation/strategy/analysis1.html'

    algorithm_result = AlgorithmResult.objects.get(id=algorithmresult_id)

    if request.method == 'POST':
        form = StrategyAnalysisForm1(request.POST)
        if form.is_valid():
            return redirect(reverse('admin:strategy_analysis2', args=(
                int(form.cleaned_data['algorithmresult_id']),
                int(form.cleaned_data['strategy'])
            )))
    else:
        form = StrategyAnalysisForm1(
            initial={
                'algorithmresult_id': algorithmresult_id,
                'symbol': algorithm_result.symbol,
                'algorithm_id': algorithm_result.algorithm.id,
                'algorithm_rule': algorithm_result.algorithm.rule,
                'algorithm_args': algorithm_result.arguments,
                'sharpe_ratio': algorithm_result.sharpe_spy,
                'probability': 'Profit: {profit} ; Loss: {loss}'.format(
                    profit=algorithm_result.profit_prob,
                    loss=algorithm_result.loss_prob
                ),
                'profit_loss': 'Sum: {pl_sum}, CP: {pl_cumprod}, Mean: {pl_mean}'.format(
                    pl_sum=algorithm_result.pl_sum,
                    pl_cumprod=algorithm_result.pl_cumprod,
                    pl_mean=algorithm_result.pl_mean,
                ),
                'risk': 'Max DD: {max_dd}, VaR 99%: {var99}'.format(
                    max_dd=algorithm_result.max_dd,
                    var99=algorithm_result.var_pct99
                )

            }
        )

        underlying = Underlying.objects.get(symbol=algorithm_result.symbol)
        if not algorithm_result.algorithm.optionable or not underlying.option:
            form.fields['strategy'].choices = Strategy.objects.exclude(
                instrument__in=('Covered', 'Option')
            ).order_by('id').reverse().values_list('id', 'name')

    parameters = dict(
        site_title='Simulation analysis',
        title='Simulation analysis - select strategy',
        form=form
    )

    return render(request, template, parameters)


# noinspection PyUnresolvedReferences,PyUnusedLocal
class StrategyAnalysisForm2(forms.Form):
    symbol = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))
    algorithm_name = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))
    algorithm_args = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))

    strategy = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control vTextField', 'readonly': 'readonly'}
    ))

    strategy_id = forms.IntegerField(widget=forms.HiddenInput())
    algorithmresult_id = forms.IntegerField(widget=forms.HiddenInput())

    capital = forms.DecimalField(widget=forms.NumberInput(
        attrs={'class': 'form-control vTextField'}
    ))

    commission = forms.ChoiceField(
        widget=forms.Select(
            attrs={'class': 'form-control vTextField'}
        )
    )

    def __init__(self, *args, **kwargs):
        arguments = kwargs.pop('arguments')
        super(StrategyAnalysisForm2, self).__init__(*args, **kwargs)

        self.fields['commission'].choices = [
            (commission.id, commission.__unicode__())
            for commission in Commission.objects.all()
        ]

        for arg, default in arguments:
            #print arg, zip(value, value)
            if type(default) == tuple:
                if all([type(d) == bool for d in default]):
                    choices = [(int(key), str(value).upper()) for key, value in zip(default, default)]
                else:
                    choices = [(key, value.upper()) for key, value in zip(default, default)]

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

    def clean(self):
        """
        Validate input data
        """
        cleaned_data = super(StrategyAnalysisForm2, self).clean()

        # make sure argument result exists
        algorithmresult_id = cleaned_data['algorithmresult_id']
        try:
            AlgorithmResult.objects.get(id=algorithmresult_id)
        except ObjectDoesNotExist:
            self._errors['algorithmresult_id'] = self.error_class(
                ['Algorithm result id does not exists.']
            )

        # make sure strategy result exists
        strategy_id = cleaned_data['strategy_id']
        try:
            strategy = Strategy.objects.get(id=strategy_id)
        except ObjectDoesNotExist:
            self._errors['strategy_id'] = self.error_class(
                ['Strategy id does not exists.']
            )
        else:
            # make sure strategy arguments is valid
            arguments = strategy.get_args()

            for arg, default in arguments:
                try:
                    # note: select field already have choices validation
                    data = cleaned_data[arg]

                    if type(default) != tuple:
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

        # capital
        capital = cleaned_data['capital']
        try:
            capital = float(capital)

            if capital < 0:
                raise ValueError()

        except ValueError:
            self._errors['capital'] = self.error_class(
                ['Capital must be a positive value.']
            )

        # commission
        commission = cleaned_data['commission']
        try:
            Commission.objects.get(id=int(commission))
        except (ValueError, ObjectDoesNotExist) as e:
            self._errors['commission'] = self.error_class(
                ['Commission does not exists.']
            )

        return cleaned_data

    def analysis(self):
        """
        Create strategy analysis reports then save into db
        """
        cleaned_data = self.clean()

        # strategy args
        data_keys = (
            'algorithm_name', 'symbol', 'strategy', 'commission',
            'algorithmresult_id', 'capital', 'algorithm_args', 'strategy_id'
        )
        fields = {key: value for key, value in cleaned_data.items()
                  if key not in data_keys}

        # start strategy quant
        strategy_quant = StrategyQuant(
            algorithmresult_id=cleaned_data['algorithmresult_id'],
            strategy_id=cleaned_data['strategy_id'],
            commission_id=cleaned_data['commission'],
            capital=cleaned_data['capital']
        )
        strategy_quant.set_args(fields)

        reports = strategy_quant.make_reports()

        strategy_results = list()
        for report in reports:
            for key in ('pct_bull', 'pct_even', 'pct_bear'):
                del report[key]

            strategy_result = StrategyResult(**report)
            strategy_result.symbol = strategy_quant.algorithm_result.symbol
            strategy_result.algorithm_result = strategy_quant.algorithm_result
            strategy_result.strategy = strategy_quant.strategy
            strategy_result.commission = strategy_quant.commission
            strategy_results.append(strategy_result)
        else:
            StrategyResult.objects.bulk_create(strategy_results)


def strategy_analysis2(request, algorithmresult_id, strategy_id):
    """
    Simulation analysis 2 for input trade arguments
    :param request: request
    :param algorithmresult_id: int
    :param strategy_id: int
    :return: render
    """
    template = 'simulation/strategy/analysis2.html'

    algorithm_result = AlgorithmResult.objects.get(id=algorithmresult_id)
    strategy = Strategy.objects.get(id=strategy_id)
    arguments = strategy.get_args()

    if request.method == 'POST':
        form = StrategyAnalysisForm2(request.POST, arguments=arguments)
        if form.is_valid():
            form.analysis()

            return redirect(reverse('admin:simulation_strategyresult_changelist'))
    else:
        # determine capital
        if strategy.category.lower() in ('stock', 'covered'):
            capital = 10000.00
        else:
            capital = 2000.00

        initial = {
            'symbol': algorithm_result.symbol,
            'algorithmresult_id': algorithm_result.id,
            'algorithm_name': algorithm_result.algorithm.rule,
            'algorithm_args': algorithm_result.arguments,
            'strategy_id': strategy.id,
            'strategy': strategy.name,
            'capital': capital
        }

        if len(strategy.arguments):
            initial.update(eval(strategy.arguments))

        form = StrategyAnalysisForm2(
            arguments=arguments,
            initial=initial
        )

    parameters = dict(
        site_title='Simulation analysis',
        title='Simulation analysis - set arguments',
        form=form,
        algorithmresult_id=algorithmresult_id
    )

    return render(request, template, parameters)












