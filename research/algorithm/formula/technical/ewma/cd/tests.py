from base.utests import TestUnitSetUp
from research.algorithm.models import Formula


# noinspection PyArgumentList
class TestEWMAChangeDirection(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.formula = Formula.objects.get(rule=rule)
        self.backtest = self.formula.start_backtest()
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.convert_data()

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.hd_args = {
            'span': 120,
            'previous': 60,
        }
        self.cs_args = {}

        self.algorithm_analysis('Ewma Chg D')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)

        print df_test.to_string(line_width=200)

        new_columns = ('ema0', 'ema1', 'ema_chg', 'signal')
        for column in new_columns:
            self.assertIn(column, df_test.columns)

    def test_create_signal(self):
        """
        Test create signal based on data frame that handle data generate
        """
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        self.df_signal = self.backtest.create_signal(df_test, **self.cs_args)

        print self.df_signal.to_string(line_width=200)

        columns = ('date0', 'date1', 'signal0', 'signal1',
                   'close0', 'close1', 'holding', 'pct_chg')

        for column in columns:
            self.assertIn(column, self.df_signal.columns)


# noinspection PyArgumentList
class TestEWMAChangeDirectionReverse(TestEWMAChangeDirection):
    def setUp(self):
        TestEWMAChangeDirection.setUp(self)

        self.algorithm_analysis('Ewma Chg D - R')


# noinspection PyArgumentList
class TestEWMAChangeDirectionHoldingPeriod(TestEWMAChangeDirection):
    def setUp(self):
        TestEWMAChangeDirection.setUp(self)

        self.hd_args = {'span': 120, 'previous': 20}
        self.cs_args = {'holding': 20}

        self.algorithm_analysis('Ewma Chg D - H')


# noinspection PyArgumentList
class TestEWMAChangeDirectionUpOnly(TestEWMAChangeDirection):
    def setUp(self):
        TestEWMAChangeDirection.setUp(self)

        self.algorithm_analysis('Ewma Chg D - UP')


# noinspection PyArgumentList
class TestEWMAChangeDirectionDownOnly(TestEWMAChangeDirection):
    def setUp(self):
        TestEWMAChangeDirection.setUp(self)

        self.algorithm_analysis('Ewma Chg D - DW')


# noinspection PyArgumentList
class TestEWMAChangeDirectionAfter2Days(TestEWMAChangeDirection):
    def setUp(self):
        TestEWMAChangeDirection.setUp(self)

        self.algorithm_analysis('Ewma Chg D - AD')
        self.cs_args = {'after': 5}

    def test_create_signal(self):
        TestEWMAChangeDirection.test_create_signal(self)

        for holding in self.df_signal['holding']:
            self.assertGreaterEqual(holding.days, self.cs_args['after'])


# noinspection PyArgumentList
class TestEWMAChangeDirectionUpHolding(TestEWMAChangeDirection):
    def setUp(self):
        TestEWMAChangeDirection.setUp(self)

        self.hd_args = {'span': 120, 'previous': 20}
        self.cs_args = {'holding': 20}

        self.algorithm_analysis('Ewma Chg D - UP H')