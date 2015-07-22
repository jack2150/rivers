from base.utests import TestUnitSetUp
from quantitative.models import Algorithm
from simulation.models import Strategy
from simulation.strategy.covered.covered_call import *


class TestStrategyCoveredCall(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.algorithm = Algorithm.objects.get(rule='Options Day to Expire')
        # self.algorithm = Algorithm.objects.get(rule='EWMA change direction - H')

        self.quant = self.algorithm.make_quant()
        self.quant.seed_data(self.symbol)
        self.hd_args = {'dte': 45}
        self.cs_args = {'side': 'buy'}
        #self.hd_args = {'span': 60, 'previous': 20}
        #self.cs_args = {'holding': 20}

        self.strategy = Strategy.objects.get(name='Covered Call by Cycle Strike')
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


class TestStrategyCoveredPut(TestStrategyCoveredCall):
    def setUp(self):
        TestStrategyCoveredCall.setUp(self)

        self.strategy = Strategy.objects.get(name='Covered Put by Cycle Strike')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }


class TestStrategyProtectiveCall(TestStrategyCoveredCall):
    def setUp(self):
        TestStrategyCoveredCall.setUp(self)

        self.strategy = Strategy.objects.get(name='Protective Call by Cycle Strike')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }


class TestStrategyProtectivePut(TestStrategyCoveredCall):
    def setUp(self):
        TestStrategyCoveredCall.setUp(self)

        self.strategy = Strategy.objects.get(name='Protective Put by Cycle Strike')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }
