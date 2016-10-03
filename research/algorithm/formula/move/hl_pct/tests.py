from base.utests import TestUnitSetUp
from research.algorithm.models import Formula


# noinspection PyArgumentList
class TestMoveDaySwing(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.formula = Formula.objects.get(rule=rule)

        self.backtest = self.formula.start_backtest()
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.convert_data()

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

        self.backtest = None
        self.algorithm_analysis('Day Swing')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        for close in ('higher', 'lower'):
            print 'close:', close
            self.hd_args['close'] = close
            self.df_stock = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
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
        self.df_stock = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)

        for side in ('buy', 'sell'):
            self.cs_args['side'] = side
            self.df_signal = self.backtest.create_signal(self.df_stock, **self.cs_args)

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
        self.backtest = None
        self.algorithm_analysis('Day Swing Distance')

    def test_handle_data(self):
        for close in ('higher', 'lower'):
            self.hd_args['close'] = close
            self.df_stock = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
            print self.df_stock.to_string(line_width=400)

            new_columns = ('found0', 'found1', 'high_to_low', 'open_to_close')
            for column in new_columns:
                self.assertIn(column, self.df_stock.columns)