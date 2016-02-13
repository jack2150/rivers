from django.db import models
from importlib import import_module
from inspect import getargspec


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


class Trade(models.Model):
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

    def get_order(self):
        """
        Import module then get method and make quant class
        :return: Quant
        """
        create_order = None
        if self.id:
            path = 'research.strategy.trade.{path}'.format(path=self.path)
            module = import_module(path)
            create_order = getattr(module, 'create_order')

        return create_order

    def get_args(self):
        """
        Get argument from strategy trade method
        :return: dict
        """
        module = import_module('research.strategy.trade.{path}'.format(path=self.path))
        create_order = getattr(module, 'create_order')

        specs = getargspec(create_order)

        arg_names = [a for a in specs.args if a not in (
            'df_stock', 'df_signal', 'df_contract', 'df_option', 'df_all'
        )]

        return [(k, v) for k, v in zip(arg_names, specs.defaults)]

    def __unicode__(self):
        return '{name}'.format(name=self.name)


class TradeResult(models.Model):
    symbol = models.CharField(max_length=50)
