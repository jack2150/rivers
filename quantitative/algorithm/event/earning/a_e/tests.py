from base.utests import TestUnitSetUp
from quantitative.models import Algorithm


# noinspection PyArgumentList
class TestEarningMovementDirection(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.algorithm = Algorithm.objects.get(rule=rule)

        self.quant = self.algorithm.make_quant()

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'YUM'  # jpm before, fslr after
        self.hd_args = {
            'move': 'down',
            'percent': 5,
            'bdays': 30
        }
        self.cs_args = {
            'side': 'sell'
        }

        self.quant = None
        self.algorithm_analysis('After Earning Move')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        df = self.quant.make_df(self.symbol)

        df_stock = self.quant.handle_data(df, **self.hd_args)

        print df_stock.to_string(line_width=200)

        new_columns = ('earning', 'found', 'date1', 'close1')
        for column in new_columns:
            self.assertIn(column, df_stock.columns)

    def test_create_signal(self):
        """
        Test create signal based on data frame that handle data generate
        """
        df = self.quant.make_df(self.symbol)
        df_stock = self.quant.handle_data(df, **self.hd_args)
        df_signal = self.quant.create_signal(df_stock, **self.cs_args)

        print df_signal.to_string(line_width=200)

        columns = ('date0', 'date1', 'signal0', 'signal1',
                   'close0', 'close1', 'holding', 'pct_chg')

        for column in columns:
            self.assertIn(column, df_signal.columns)
