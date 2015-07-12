from importlib import import_module
from inspect import getargspec
from django.db import models
import pandas as pd
import numpy as np
from quantitative.models import Algorithm, AlgorithmResult


class Commission(models.Model):
    company = models.CharField(max_length=200, help_text='Brokerage company name.')
    plan = models.IntegerField(help_text='Company fees plan.')

    stock_order_fee = models.DecimalField(
        max_digits=6, decimal_places=2, help_text='Once per stock order.'
    )
    stock_brokerage_fee = models.FloatField(help_text='In percentage.')

    option_order_fee = models.DecimalField(
        max_digits=6, decimal_places=2, help_text='Once per option order.'
    )
    option_contract_fee = models.DecimalField(
        max_digits=6, decimal_places=2, help_text='Charge per option contract.'
    )

    def __unicode__(self):
        return '{company} {plan} Stock: {s_order}, Option: {o_order} + {o_contract}'.format(
            company=self.company.split(' ')[0], plan=self.plan, s_order=self.stock_order_fee,
            o_order=self.option_order_fee, o_contract=self.option_contract_fee
        )


# noinspection PyUnresolvedReferences
class Strategy(models.Model):
    name = models.CharField(max_length=100, help_text='Strategy name.')
    instrument = models.CharField(
        max_length=10, help_text='Instrument for this strategy.',
        choices=(('Stock', 'Stock'), ('Covered', 'Covered'), ('Option', 'Option'))
    )
    category = models.CharField(
        max_length=10, help_text='Strategy category.'
    )
    description = models.TextField(null=True, blank=True, default='',
                                   help_text='Explain how this strategy work.')
    path = models.CharField(max_length=200, help_text='Path to strategy module.')
    arguments = models.TextField(null=True, blank=True, default='',
                                 help_text='Default arguments.')

    def get_args(self):
        """
        Get argument from strategy trade method
        :return: dict
        """
        module = import_module('simulation.strategy.{path}'.format(path=self.path))
        create_order = getattr(module, 'create_order')

        specs = getargspec(create_order)

        arg_names = [a for a in specs.args if a not in ('df_stock', 'df_signal')]

        return [(k, v) for k, v in zip(arg_names, specs.defaults)]

    def make_order(self, df_stock, df_signal, *args, **kwargs):
        """
        Run strategy trade
        :param args:
        :param kwargs:
        :return:
        """
        module = import_module('simulation.strategy.{path}'.format(path=self.path))
        create_order = getattr(module, 'create_order')

        df_order = create_order(df_stock, df_signal, *args, **kwargs)

        # format df_order
        df_order['close0'] = df_order['close0'].astype(np.float64)
        df_order['holding'] = df_order['holding'].apply(
            lambda x: int(x.astype('timedelta64[D]') / np.timedelta64(1, 'D'))
        )
        df_order['holding'] = df_order['holding'].astype(np.int)

        return df_order

    def __unicode__(self):
        return '{name}'.format(name=self.name)


class StrategyResult(models.Model):
    """
    An algorithm contain different of variables test
    """
    symbol = models.CharField(max_length=20)
    date = models.DateField(default=pd.datetime.today().date())

    algorithm_result = models.ForeignKey(AlgorithmResult)
    strategy = models.ForeignKey(Strategy)
    arguments = models.CharField(max_length=500)
    commission = models.ForeignKey(Commission)

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

    df_trade = models.TextField()
    df_cumprod = models.TextField()

    capital0 = models.DecimalField(max_digits=10, decimal_places=2)
    capital1 = models.DecimalField(max_digits=10, decimal_places=2)
    cumprod1 = models.DecimalField(max_digits=10, decimal_places=2)
    remain_mean = models.DecimalField(max_digits=10, decimal_places=2)
    cp_remain_mean = models.DecimalField(max_digits=10, decimal_places=2)

    roi_sum = models.DecimalField(max_digits=10, decimal_places=2)
    roi_mean = models.DecimalField(max_digits=10, decimal_places=2)
    cp_roi_sum = models.DecimalField(max_digits=10, decimal_places=2)
    cp_roi_mean = models.DecimalField(max_digits=10, decimal_places=2)

    fee_sum = models.DecimalField(max_digits=10, decimal_places=2)
    fee_mean = models.DecimalField(max_digits=10, decimal_places=2)

    def __unicode__(self):
        return '{strategy}: {sharpe_spy} {trades} {profit_prob}'.format(
            strategy=self.strategy,
            sharpe_spy=self.sharpe_spy,
            trades=self.trades,
            profit_prob=self.profit_prob
        )
