from importlib import import_module
from django.db import models


class Algorithm(models.Model):
    """
    An algorithm is script that keep 2 section method
    """
    rule = models.CharField(max_length=200)
    formula = models.CharField(max_length=200)
    date = models.DateField()

    category = models.CharField(max_length=200)
    method = models.CharField(max_length=200)
    path = models.CharField(max_length=200)

    description = models.TextField(null=True, blank=True)

    def get_module(self):
        """
        Import module then get handle_data and create_signal method
        :rtype : tuple of function
        """
        path = 'quant.algorithm.{path}'.format(path=self.path)

        module = import_module(path)
        handle_data = getattr(module, 'handle_data')
        create_signal = getattr(module, 'create_signal')

        return handle_data, create_signal

    def __unicode__(self):
        return self.rule


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

    signals = models.TextField()


