from base.utests import TestUnitSetUp
from quantitative.models import Algorithm
import pandas as pd
from simulation.models import Strategy


class TestStrategyLongCall(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.algorithm = Algorithm.objects.get(rule='Options Day to Expire')

        self.quant = self.algorithm.make_quant()
        self.quant.seed_data(self.symbol)
        self.hd_args = {'dte': 45}
        self.cs_args = {'side': 'buy'}

        self.strategy = Strategy.objects.get(name='Long Call')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }

    def test_make_order(self):
        """
        Test trade using stop loss order
        """

        df_stock = self.quant.handle_data(self.quant.data[self.symbol], **self.hd_args)
        df_signal = self.quant.create_signal(df_stock, **self.cs_args)

        self.strategy.make_order(df_stock, df_signal, **self.args)

        # todo: until here
