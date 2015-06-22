from base.utests import TestUnitSetUp
from quant.analysis import Quant
from quant.models import Algorithm


# noinspection PyArgumentList
class TestEWMAChangeDirection(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.algorithm = Algorithm.objects.get(rule=rule)

        handle_data, create_signal = self.algorithm.get_module()

        self.quant = Quant()
        self.quant.handle_data = handle_data
        self.quant.create_signal = create_signal

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.hd_args = {
            'span': 120,
            'previous': 20
        }
        self.cs_args = {}

        self.quant = None
        self.algorithm_analysis('EWMA change of direction')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        df = self.quant.make_df(self.symbol)

        df_stock = self.quant.handle_data(df, **self.hd_args)

        print df_stock.tail().to_string(line_width=200)

        new_columns = ('ema0', 'ema1', 'ema_chg', 'signal')
        for column in new_columns:
            self.assertIn(column, df_stock.columns)

    def test_create_signal(self):
        """
        Test create signal based on data frame that handle data generate
        """
        df = self.quant.make_df(self.symbol)
        df_stock = self.quant.handle_data(df, **self.hd_args)
        df_signal = self.quant.create_signal(df_stock, **self.cs_args)

        print df_signal.tail().to_string(line_width=200)

        columns = ('date0', 'date1', 'signal0', 'signal1',
                   'close0', 'close1', 'holding', 'pct_chg')

        for column in columns:
            self.assertIn(column, df_signal.columns)


# noinspection PyArgumentList
class TestEWMAChangeDirectionReverse(TestEWMAChangeDirection):
    def setUp(self):
        TestEWMAChangeDirection.setUp(self)

        self.algorithm_analysis('EWMA change of direction - Reverse')


# noinspection PyArgumentList
class TestEWMAChangeDirectionHoldingPeriod(TestEWMAChangeDirection):
    def setUp(self):
        TestEWMAChangeDirection.setUp(self)

        self.hd_args = {'span': 120, 'previous': 20}
        self.cs_args = {'holding_period': 20}

        self.algorithm_analysis('EWMA change of direction - Holding Period')


# noinspection PyArgumentList
class TestEWMAChangeDirectionUpOnly(TestEWMAChangeDirection):
    def setUp(self):
        TestEWMAChangeDirection.setUp(self)

        self.algorithm_analysis('EWMA change of direction - Up Only')


# noinspection PyArgumentList
class TestEWMAChangeDirectionDownOnly(TestEWMAChangeDirection):
    def setUp(self):
        TestEWMAChangeDirection.setUp(self)

        self.algorithm_analysis('EWMA change of direction - Down Only')
