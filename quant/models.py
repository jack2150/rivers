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
    fname = models.CharField(max_length=200)

    description = models.TextField(null=True, blank=True)

    def get_module(self):
        """
        Import module then get handle_data and create_signal method
        :rtype : tuple of function
        """
        path = 'quant.algorithm.{category}.{method}.{fname}'.format(
            category=self.category,
            method=self.method,
            fname=self.fname.replace('.py', '')
        )

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
    sharpe_spy = models.FloatField()
    sortino_rf = models.FloatField()
    sortino_spy = models.FloatField()

    buy_hold = models.FloatField()

    trades = models.IntegerField()
    profit_trades = models.IntegerField()
    profit_prob = models.FloatField()
    loss_trades = models.IntegerField()
    loss_prob = models.FloatField()
    max_profit = models.FloatField()
    max_loss = models.FloatField()

    sum_result = models.FloatField()
    cumprod_result = models.FloatField()
    mean_result = models.FloatField()

    var_pct99 = models.FloatField(verbose_name='VaR 99%')
    var_pct95 = models.FloatField(verbose_name='VaR 95%')

    signals = models.TextField()
