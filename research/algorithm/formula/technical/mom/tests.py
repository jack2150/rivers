from base.utests import TestUnitSetUp
from research.algorithm.models import Formula


# noinspection PyArgumentList
class TestMomentum(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.formula = Formula.objects.get(rule=rule)

        self.backtest = self.formula.start_backtest()
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.get_data()

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.hd_args = {
            'span': 60
        }
        self.cs_args = {}

        self.backtest = None
        self.algorithm_analysis('Momentum rule')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        df_stock = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)

        print df_stock.to_string(line_width=200)

        new_columns = ('close0', 'net_chg', 'signal')
        for column in new_columns:
            self.assertIn(column, df_stock.columns)

    def test_create_signal(self):
        """
        Test create signal based on data frame that handle data generate
        """
        df_test = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        df_signal = self.backtest.create_signal(df_test, **self.cs_args)

        print df_signal.to_string(line_width=200)

        columns = ('date0', 'date1', 'signal0', 'signal1',
                   'close0', 'close1', 'holding', 'pct_chg')

        for column in columns:
            self.assertIn(column, df_signal.columns)


# noinspection PyArgumentList
class TestMomentumHolding(TestMomentum):
    def setUp(self):
        TestMomentum.setUp(self)

        self.cs_args = {'holding': 20}
        self.algorithm_analysis('Momentum rule - H')


# noinspection PyArgumentList
class TestMomentumUpHolding(TestMomentum):
    def setUp(self):
        TestMomentum.setUp(self)

        self.cs_args = {'holding': 20}
        self.algorithm_analysis('Momentum rule - UP H')


# noinspection PyArgumentList
class TestMomentumDownHolding(TestMomentum):
    def setUp(self):
        TestMomentum.setUp(self)

        self.cs_args = {'holding': 20}
        self.algorithm_analysis('Momentum rule - DW H')