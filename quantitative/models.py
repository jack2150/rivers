from importlib import import_module
from inspect import getargspec
from django.db import models
from quantitative.quant import AlgorithmQuant


class Algorithm(models.Model):
    """
    An algorithm is script that keep 2 section method
    """
    rule = models.CharField(max_length=200)
    formula = models.CharField(max_length=200)
    date = models.DateField()

    category = models.CharField(
        max_length=10,
        choices=(('Stock', 'Stock'), ('Covered', 'Covered'), ('Option', 'Option'))
    )
    method = models.CharField(max_length=200)
    path = models.CharField(max_length=200)

    description = models.TextField(null=True, blank=True, default='')

    def __init__(self, *args, **kwargs):
        super(Algorithm, self).__init__(*args, **kwargs)

        if self.id:
            self.quant = self.make_quant()
        else:
            self.quant = AlgorithmQuant(self)

    def make_quant(self):
        """
        Import module then get method and make quant class
        :return: Quant
        """
        path = 'quantitative.algorithm.{path}'.format(path=self.path)

        module = import_module(path)
        handle_data = getattr(module, 'handle_data')
        create_signal = getattr(module, 'create_signal')

        quant = AlgorithmQuant(self)
        quant.handle_data = handle_data
        quant.create_signal = create_signal

        return quant

    def get_args(self):
        """
        Get handle_data and create_signal arguments
        :return: tuple(handle_data_args, create_signal_args)
        """
        path = 'quantitative.algorithm.{path}'.format(path=self.path)

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

        return ([('handle_data_%s' % k, v) for k, v in hd_args]
                + [('create_signal_%s' % k, v) for k, v in cs_args])

    def __unicode__(self):
        return self.rule


class AlgorithmArgument(models.Model):
    """
    An algorithm contain more than on arguments
    It can be use to direct run test without input args
    """
    algorithm = models.ForeignKey(Algorithm)

    arguments = models.TextField()
    level = models.CharField(max_length=20, choices=(
        ('Fast', 'Fast'), ('Simple', 'Simple'), ('Deep', 'Deep')
    ))
    result = models.CharField(max_length=20, choices=(
        ('Bad', 'Bad'), ('Normal', 'Normal'), ('Good', 'Good')
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


class AlgorithmResult(models.Model):
    """
    An algorithm contain different of variables test
    """
    symbol = models.CharField(max_length=20)
    date = models.DateField()

    algorithm = models.ForeignKey(Algorithm)
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

    df_signal = models.TextField()

    def __unicode__(self):
        return 'AlgorithmResult: {sharpe_spy} {trades} {profit_prob}'.format(
            sharpe_spy=self.sharpe_spy,
            trades=self.trades,
            profit_prob=self.profit_prob
        )
