from base.utests import TestUnitSetUp
from research.algorithm.models import Formula


# noinspection PyArgumentList
class TestBasicPercentMove(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.algorithm = Formula.objects.get(rule=rule)

        self.quant = self.algorithm.start_backtest()

        self.df = None
        self.df_stock = None
        self.df_signal = None

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'EBAY'
        self.hd_args = {
            'move': 'down',
            'pct_from': 5,
            'pct_to': 10,
            'bdays': 30,
        }
        self.cs_args = {
            'side': 'buy',
        }

        self.quant = None
        self.algorithm_analysis('Basic % Move')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        self.df = self.quant.make_df(self.symbol)
        self.df_stock = self.quant.handle_data(self.df, **self.hd_args)

        print self.df_stock.to_string(line_width=200)

        new_columns = ('found', 'date1', 'close1')
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

            print '=' * 100