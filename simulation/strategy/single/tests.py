from base.utests import TestUnitSetUp
from quantitative.models import Algorithm
from simulation.models import Strategy
import numpy as np


class TestStrategyLongCall(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'FSLR'
        self.algorithm = Algorithm.objects.get(rule='Options DTE - No Dup')
        #self.algorithm = Algorithm.objects.get(rule='EWMA change direction - H')

        self.quant = self.algorithm.make_quant()
        self.quant.seed_data(self.symbol)
        self.hd_args = {'dte': 45}
        self.cs_args = {'side': 'buy'}
        #self.hd_args = {'span': 60, 'previous': 20}
        #self.cs_args = {'holding': 20}

        self.strategy = Strategy.objects.get(name='Long Call CS')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }

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
        for expire in (False, True):
            print 'expire set:', expire

            df_order = self.strategy.make_order(df_stock, df_signal, expire=expire, **self.args)
            df_order['diff'] = df_order['stock0'] - df_order['strike']

            print df_order.to_string(line_width=300)

            pct_chg = df_order['pct_chg']
            pct_chg = pct_chg[pct_chg < 10]
            print pct_chg.sum(), np.round(pct_chg.mean(), 2),
            print np.round(float(pct_chg[pct_chg > 0].count() / float(pct_chg.count())), 2),
            print np.round(float(pct_chg[pct_chg < 0].count() / float(pct_chg.count())), 2)

            print '-' * 100 + '\n'


class TestStrategyLongPut(TestStrategyLongCall):
    def setUp(self):
        TestStrategyLongCall.setUp(self)

        self.strategy = Strategy.objects.get(name='Long Put CS')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }


class TestStrategyNakedCall(TestStrategyLongCall):
    def setUp(self):
        TestStrategyLongCall.setUp(self)

        self.strategy = Strategy.objects.get(name='Naked Call CS')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }


class TestStrategyNakedPut(TestStrategyLongCall):
    def setUp(self):
        TestStrategyLongCall.setUp(self)

        self.strategy = Strategy.objects.get(name='Naked Put CS')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 5
        }
