from base.utests import TestUnitSetUp
from quantitative.models import Algorithm
from simulation.models import Strategy
import numpy as np


class TestStrategyLongCallVertical(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'JPM'
        self.algorithm = Algorithm.objects.get(rule='Options Day to Expire')
        # self.algorithm = Algorithm.objects.get(rule='EWMA change direction - H')

        self.quant = self.algorithm.make_quant()
        self.quant.seed_data(self.symbol)
        self.hd_args = {'dte': 45}
        self.cs_args = {'side': 'buy'}
        #self.hd_args = {'span': 60, 'previous': 20}
        #self.cs_args = {'holding': 20}

        self.strategy = Strategy.objects.get(name='Long Call Vertical CS')

    def test_make_order(self):
        """
        Test trade using stop loss order
        import profile
        # profile.runctx('self.strategy.make_order(
        df_stock, df_signal, expire=expire, **self.args)', globals(), locals())
        """
        args = ({'moneyness': 'OTM', 'cycle': 0, 'strike': 0, 'wide': 1},
                {'moneyness': 'ITM', 'cycle': 0, 'strike': 0, 'wide': 1},
                {'moneyness': 'ATM', 'cycle': 0, 'strike': 0, 'wide': 0},)

        df_stock = self.quant.handle_data(self.quant.data[self.symbol], **self.hd_args)
        df_signal = self.quant.create_signal(df_stock, **self.cs_args)

        for expire in (False, True)[:1]:
            for arg in args:
                print 'expire set:', expire, 'arg:', arg

                df_order = self.strategy.make_order(df_stock, df_signal, expire=expire, **arg)

                print df_order.to_string(line_width=300)

                pct_chg = df_order['pct_chg']
                pct_chg = pct_chg[pct_chg < 10]
                print pct_chg.sum(), np.round(pct_chg.mean(), 2),
                print np.round(float(pct_chg[pct_chg > 0].count() / float(pct_chg.count())), 2),
                print np.round(float(pct_chg[pct_chg < 0].count() / float(pct_chg.count())), 2)

                print len(df_signal), len(df_order), len(df_signal) == len(df_order)

                self.assertTrue(len(df_order))

                print '-' * 100 + '\n'


class TestStrategyLongPutVertical(TestStrategyLongCallVertical):
    def setUp(self):
        TestStrategyLongCallVertical.setUp(self)

        self.strategy = Strategy.objects.get(name='Long Put Vertical CS')


class TestStrategyShortCallVertical(TestStrategyLongCallVertical):
    def setUp(self):
        TestStrategyLongCallVertical.setUp(self)

        self.strategy = Strategy.objects.get(name='Short Call Vertical CS')


class TestStrategyShortPutVertical(TestStrategyLongCallVertical):
    def setUp(self):
        TestStrategyLongCallVertical.setUp(self)

        self.strategy = Strategy.objects.get(name='Short Put Vertical CS')