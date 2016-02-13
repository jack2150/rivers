from base.utests import TestUnitSetUp
from research.algorithm.models import Formula


# noinspection PyArgumentList
class TestBasicPercentMove(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.formula = Formula.objects.get(rule=rule)

        self.backtest = self.formula.start_backtest()
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2014-12-31')
        self.backtest.get_data()

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.hd_args = {
            'peak': 'high',
            'pct_move': 1.5,
            'pct_range': 0.1,
            'bdays': 5
        }
        self.cs_args = {
            'side': 'buy',
        }

        self.algorithm_analysis('Peak/Bottom Close')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        for peak in ('high', 'low'):
            print 'peak:', peak
            self.hd_args['peak'] = peak
            self.df_stock = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)

            print self.df_stock.to_string(line_width=200)

            new_columns = ('found', 'date1', 'close1')
            for column in new_columns:
                self.assertIn(column, self.df_stock.columns)

    def test_create_signal(self):
        """
        Test create signal based on data frame that handle data generate
        """
        for peak, side in (('high', 'buy'), ('low', 'sell')):
            print 'peak:', peak, 'side', side
            self.hd_args['peak'] = peak
            self.df_stock = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
            self.cs_args['side'] = side
            self.df_signal = self.backtest.create_signal(self.df_stock, **self.cs_args)

            print self.df_signal.to_string(line_width=400)

            columns = ('date0', 'date1', 'signal0', 'signal1',
                       'close0', 'close1', 'holding', 'pct_chg')

            for column in columns:
                self.assertIn(column, self.df_signal.columns)

            print '=' * 100