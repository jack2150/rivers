from base.utests import TestUnitSetUp
from research.algorithm.models import Formula
from simulation.models import Strategy


class TestStrategyCoveredCall(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.algorithm = Formula.objects.get(rule='Options DTE - No Dup')
        # self.algorithm = Algorithm.objects.get(rule='EWMA change direction - H')

        self.quant = self.algorithm.start_backtest()
        self.quant.seed_data(self.symbol)
        self.hd_args = {'dte': 45}
        self.cs_args = {'side': 'buy'}

        self.strategy = Strategy.objects.get(name='Covered Call CS')
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

        self.strategy = Strategy.objects.get(name='Covered Put CS')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }


class TestStrategyProtectiveCall(TestStrategyCoveredCall):
    def setUp(self):
        TestStrategyCoveredCall.setUp(self)

        self.strategy = Strategy.objects.get(name='Protective Call CS')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }


class TestStrategyProtectivePut(TestStrategyCoveredCall):
    def setUp(self):
        TestStrategyCoveredCall.setUp(self)

        self.strategy = Strategy.objects.get(name='Protective Put CS')
        self.args = {
            'moneyness': 'OTM',
            'cycle': 0,
            'strike': 0
        }
