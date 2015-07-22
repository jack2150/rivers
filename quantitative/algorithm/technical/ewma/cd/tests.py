from base.utests import TestUnitSetUp
from quantitative.models import Algorithm


# noinspection PyArgumentList
class TestEWMAChangeDirection(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.algorithm = Algorithm.objects.get(rule=rule)

        self.quant = self.algorithm.make_quant()

        self.df = None
        self.df_stock = None
        self.df_signal = None

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.hd_args = {
            'span': 20,
            'previous': 20
        }
        self.cs_args = {}

        self.quant = None
        self.algorithm_analysis('Ewma Chg D')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        self.df = self.quant.make_df(self.symbol)
        self.df_stock = self.quant.handle_data(self.df, **self.hd_args)

        print self.df_stock.to_string(line_width=200)

        new_columns = ('ema0', 'ema1', 'ema_chg', 'signal')
        for column in new_columns:
            self.assertIn(column, self.df_stock.columns)

    def test_create_signal(self):
        """
        Test create signal based on data frame that handle data generate
        """
        self.df = self.quant.make_df(self.symbol)
        self.df_stock = self.quant.handle_data(self.df, **self.hd_args)
        self.df_signal = self.quant.create_signal(self.df_stock, **self.cs_args)

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
            self.assertGreaterEqual(holding, self.cs_args['after'])


# noinspection PyArgumentList
class TestEWMAChangeDirectionUpHolding(TestEWMAChangeDirection):
    def setUp(self):
        TestEWMAChangeDirection.setUp(self)

        self.hd_args = {'span': 120, 'previous': 20}
        self.cs_args = {'holding': 20}

        self.algorithm_analysis('Ewma Chg D - UP H')