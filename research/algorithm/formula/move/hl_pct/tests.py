from base.utests import TestUnitSetUp
from research.algorithm.models import Formula


# noinspection PyArgumentList
class TestMoveDaySwing(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.algorithm = Formula.objects.get(rule=rule)

        self.quant = self.algorithm.start_backtest()

        self.df = None
        self.df_stock = None
        self.df_signal = None

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'SPY'
        self.hd_args = {
            'pct_up': 1,
            'pct_down': -1.5,
            'close': 'higher',
            'bdays': 5
        }
        self.cs_args = {
            'side': 'buy',
        }

        self.quant = None
        self.algorithm_analysis('Day Swing')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        self.df = self.quant.make_df(self.symbol)

        for close in ('higher', 'lower'):
            print 'close:', close
            self.hd_args['close'] = close
            self.df_stock = self.quant.handle_data(self.df, **self.hd_args)
            print self.df_stock.to_string(line_width=400)

            print '=' * 100

        new_columns = ('found0', 'found1', 'found2',
                       'open_to_high', 'open_to_low', 'open_to_close')
        for column in new_columns:
            self.assertIn(column, self.df_stock.columns)

    def test_create_signal(self):
        """
        Test create signal based on data frame that handle data generate
        """
        self.df = self.quant.make_df(self.symbol)
        self.df_stock = self.quant.handle_data(self.df, **self.hd_args)

        for side in ('buy', 'sell'):
            self.cs_args['side'] = side
            self.df_signal = self.quant.create_signal(self.df_stock, **self.cs_args)

            print self.df_signal.to_string(line_width=400)

            columns = ('date0', 'date1', 'signal0', 'signal1',
                       'close0', 'close1', 'holding', 'pct_chg')

            for column in columns:
                self.assertIn(column, self.df_signal.columns)

            print 'sum:', self.df_signal['pct_chg'].sum()

            print '=' * 100


# noinspection PyArgumentList
class TestMoveDaySwingDistance(TestMoveDaySwing):
    def setUp(self):
        TestMoveDaySwing.setUp(self)

        self.hd_args = {
            'distance': 2,
            'close': 'higher',
            'bdays': 5
        }
        self.quant = None
        self.algorithm_analysis('Day Swing Distance')

    def test_handle_data(self):
        self.df = self.quant.make_df(self.symbol)

        for close in ('higher', 'lower'):
            self.hd_args['close'] = close
            self.df_stock = self.quant.handle_data(self.df, **self.hd_args)
            print self.df_stock.to_string(line_width=400)

            new_columns = ('found0', 'found1', 'high_to_low', 'open_to_close')
            for column in new_columns:
                self.assertIn(column, self.df_stock.columns)