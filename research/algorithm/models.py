from importlib import import_module
from inspect import getargspec
from django.db import models
from research.algorithm.backtest import FormulaBacktest


class Formula(models.Model):
    """
    An algorithm is script that keep 2 section method
    """
    rule = models.CharField(max_length=200)
    equation = models.CharField(max_length=200, null=True, blank=True)
    date = models.DateField()

    category = models.CharField(
        max_length=10,
        choices=(('Stock', 'Stock'), ('Covered', 'Covered'), ('Option', 'Option'))
    )
    method = models.CharField(max_length=200)
    path = models.CharField(max_length=200)

    optionable = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True, default='')

    def __init__(self, *args, **kwargs):
        super(Formula, self).__init__(*args, **kwargs)

        if self.id:
            self.backtest = self.start_backtest()
        else:
            self.backtest = FormulaBacktest(self)

    def start_backtest(self):
        """
        Import module then get method and make quant class
        :return: Quant
        """
        path = 'research.algorithm.formula.{path}'.format(path=self.path)

        backtest = None
        try:
            module = import_module(path)

            handle_data = getattr(module, 'handle_data')
            create_signal = getattr(module, 'create_signal')

            backtest = FormulaBacktest(self)
            backtest.handle_data = handle_data
            backtest.create_signal = create_signal
        except (ImportError, KeyError):
            self.path = ''
            self.save()

        return backtest

    def get_args(self):
        """
        Get handle_data and create_signal arguments
        :return: tuple(handle_data_args, create_signal_args)
        """
        path = 'research.algorithm.formula.{path}'.format(path=self.path)

        module = import_module(path)
        handle_data = getattr(module, 'handle_data')
        create_signal = getattr(module, 'create_signal')

        hd_specs = getargspec(handle_data)
        cs_specs = getargspec(create_signal)

        hd_names = [a for a in hd_specs.args if a not in ('df', 'df_stock', 'df_signal')]
        try:
            hd_args = [(k, v) for k, v in zip(hd_names, hd_specs.defaults)]
        except TypeError:
            hd_args = [(k, v) for k, v in zip(hd_names, range(len(cs_specs.args[1:])))]

        cs_names = [a for a in cs_specs.args if a not in ('df', 'df_stock', 'df_signal')]
        try:
            cs_args = [(k, v) for k, v in zip(cs_names, cs_specs.defaults)]
        except TypeError:
            cs_args = [(k, v) for k, v in zip(cs_names, range(len(cs_specs.args[1:])))]

        return (
            [('handle_data_%s' % k, v) for k, v in hd_args] +
            [('create_signal_%s' % k, v) for k, v in cs_args]
        )

    def __unicode__(self):
        return self.rule


class FormulaArgument(models.Model):
    """
    An algorithm contain more than on arguments
    It can be use to direct run test without input args
    """
    formula = models.ForeignKey(Formula)

    arguments = models.TextField()
    level = models.CharField(max_length=20, default='low', choices=(
        ('low', 'Low'), ('middle', 'Middle'), ('high', 'High')
    ))
    result = models.CharField(max_length=20, default='undefined', choices=(
        ('negative', 'Negative'), ('undefined', 'Undefined'), ('positive', 'Positive')
    ))
    description = models.TextField(
        null=True, blank=True, default='', help_text='Explain this arguments.'
    )

    def get_args(self):
        """
        Get arguments dict
        :rtype : dict
        """
        return eval(self.arguments)


class FormulaResult(models.Model):
    """
    An algorithm contain different of variables test
    """
    symbol = models.CharField(max_length=20)
    formula = models.ForeignKey(Formula)

    date = models.DateField()
    arguments = models.TextField()
    length = models.IntegerField()

    def __unicode__(self):
        return '{date} < {symbol} > {formula}'.format(
            date=self.date, symbol=self.symbol, formula=self.formula.path
        )
