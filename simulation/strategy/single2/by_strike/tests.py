from base.utests import TestUnitSetUp
from data.models import Underlying
from quantitative.models import Algorithm
from simulation.models import Strategy
import numpy as np


class TestStrategyLongCall(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.algorithm = Algorithm.objects.get(rule='Options DTE - No Dup')
        # self.algorithm = Algorithm.objects.get(rule='EWMA change direction - H')

        self.quant = self.algorithm.make_quant()
        self.quant.seed_data(self.symbol)
        self.hd_args = {'dte': 45}
        self.cs_args = {'side': 'buy'}
        #self.hd_args = {'span': 60, 'previous': 20}
        #self.cs_args = {'holding': 20}

        self.strategy = Strategy.objects.get(name='Long Call by Strike')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }

        underlying = Underlying.objects.get(symbol=self.symbol)
        self.df_contract, self.df_option = underlying.get_option()

    def test_make_order(self):
        """
        Test trade using stop loss order
        import profile
        # profile.runctx('self.strategy.make_order(
        df_stock, df_signal, expire=expire, **self.args)', globals(), locals())
        """
        df_stock = self.quant.handle_data(self.quant.data[self.symbol], **self.hd_args)
        df_signal = self.quant.create_signal(df_stock, **self.cs_args)

        print 'symbol:', self.symbol
        df_order = self.strategy.make_order(
            df_stock, df_signal, self.df_contract, self.df_option, **self.args
        )

        print df_order.to_string(line_width=300)
