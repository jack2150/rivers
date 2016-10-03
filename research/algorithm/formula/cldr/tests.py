from base.utests import TestUnitSetUp
from research.algorithm.models import Formula


# noinspection PyArgumentList
class TestMonth2MonthMove(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.formula = Formula.objects.get(rule=rule)

        self.backtest = self.formula.start_backtest()
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2016-06-30')
        self.backtest.convert_data()

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'SPY'
        self.hd_args = {

        }
        self.cs_args = {
            'side': 'buy',
            'month0': 10,
            'date0': 1,
            'month1': 3,
            'date1': 31,
        }

        self.backtest = None
        self.algorithm_analysis('Month to month')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        self.df_stock = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)

        print self.df_stock.to_string(line_width=200)

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

            print 'sum:', self.df_signal['pct_chg'].sum(),
            print 'profit:', len(self.df_signal[self.df_signal['pct_chg'] > 0]),
            print 'loss:', len(self.df_signal[self.df_signal['pct_chg'] < 0])
            print '=' * 100


class TestWeek2WeekMove(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.formula = Formula.objects.get(rule=rule)

        self.backtest = self.formula.start_backtest()
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2016-06-30')
        self.backtest.convert_data()

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'SPY'
        self.hd_args = {

        }
        self.cs_args = {
            'side': 'buy',
            'weekday0': 1,
            'bdays': 4,
        }

        self.backtest = None
        self.algorithm_analysis('Weekdays')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        self.df_stock = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)

        print self.df_stock.to_string(line_width=200)

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

            print 'sum:', self.df_signal['pct_chg'].sum(),
            print 'profit:', len(self.df_signal[self.df_signal['pct_chg'] > 0]),
            print 'loss:', len(self.df_signal[self.df_signal['pct_chg'] < 0])
            print '=' * 100