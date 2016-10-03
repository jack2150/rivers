from base.utests import TestUnitSetUp
from research.algorithm.models import Formula


class TestEWMAChangeDirection(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.formula = Formula.objects.get(rule=rule)
        self.backtest = self.formula.start_backtest()
        self.backtest.set_symbol_date(self.symbol, '2010-01-01', '2014-12-31')
        self.backtest.convert_data()
        self.backtest.extra_data()

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'AIG'
        self.hd_args = {

        }
        self.cs_args = {
            'side': 'buy',
            'before': 5,
            'after': 0
        }

        self.algorithm_analysis('Earning movement')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        df_hd = self.backtest.handle_data(
            self.backtest.df_stock,
            self.backtest.df_earning,
            **self.hd_args
        )

        print df_hd.to_string(line_width=200)

    def test_create_signal(self):
        """
        Test create signal based on data frame that handle data generate
        """
        df_hd = self.backtest.handle_data(
            self.backtest.df_stock,
            self.backtest.df_earning,
            **self.hd_args
        )

        for side in ('buy', 'sell'):
            print 'side: %s' % side
            self.cs_args['side'] = side
            df_signal = self.backtest.create_signal(df_hd, **self.cs_args)

            print df_signal.to_string(line_width=200)
            print df_signal['pct_chg'].sum()

            columns = ('date0', 'date1', 'signal0', 'signal1',
                       'close0', 'close1', 'holding', 'pct_chg')

            for column in columns:
                self.assertIn(column, df_signal.columns)

            print '-' * 70
