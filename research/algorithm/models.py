from importlib import import_module
from inspect import getargspec
from django.db import models
from research.algorithm.quant import AlgorithmQuant
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

        quant = None
        try:
            module = import_module(path)

            handle_data = getattr(module, 'handle_data')
            create_signal = getattr(module, 'create_signal')

            quant = FormulaBacktest(self)
            quant.handle_data = handle_data
            quant.create_signal = create_signal
        except (ImportError, KeyError):
            self.path = ''
            self.save()

        return quant

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
    backtest = models.BooleanField(default=False)

    def get_args(self):
        """
        Get arguments dict
        :rtype : dict
        """
        return eval(self.arguments)


class AlgorithmResult(models.Model):
    """
    An algorithm contain different of variables test
    """
    symbol = models.CharField(max_length=20)
    date = models.DateField()

    algorithm = models.ForeignKey(Formula)
    arguments = models.CharField(max_length=500)

    sharpe_rf = models.FloatField()
    sharpe_spy = models.FloatField(verbose_name='Sharpe')
    sortino_rf = models.FloatField()
    sortino_spy = models.FloatField()

    bh_sum = models.FloatField(verbose_name='BH Sum')
    bh_cumprod = models.FloatField(verbose_name='BH *')

    trades = models.IntegerField()
    profit_trades = models.IntegerField()
    profit_prob = models.FloatField(verbose_name='Profit %')
    loss_trades = models.IntegerField()
    loss_prob = models.FloatField(verbose_name='Loss %')
    max_profit = models.FloatField()
    max_loss = models.FloatField()

    pl_sum = models.FloatField(verbose_name='PL Sum')
    pl_cumprod = models.FloatField(verbose_name='PL *')
    pl_mean = models.FloatField()

    var_pct99 = models.FloatField(verbose_name='VaR 99%')
    var_pct95 = models.FloatField(verbose_name='VaR 95%')

    max_dd = models.FloatField()
    r_max_dd = models.FloatField()
    max_bh_dd = models.FloatField()
    r_max_bh_dd = models.FloatField()

    pct_mean = models.FloatField()
    pct_median = models.FloatField()
    pct_max = models.FloatField()
    pct_min = models.FloatField()
    pct_std = models.FloatField()

    day_profit_mean = models.FloatField()
    day_loss_mean = models.FloatField()

    pct_bull = models.FloatField(verbose_name='Bull %')
    pct_even = models.FloatField(verbose_name='Even %')
    pct_bear = models.FloatField(verbose_name='Bear %')

    df_signal = models.TextField()

    def __unicode__(self):
        return 'AlgorithmResult: {sharpe_spy} {trades} {profit_prob}'.format(
            sharpe_spy=self.sharpe_spy,
            trades=self.trades,
            profit_prob=self.profit_prob
        )