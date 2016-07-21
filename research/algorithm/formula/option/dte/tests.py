import itertools
import numpy as np
import pandas as pd
from base.utests import TestUnitSetUp
from research.algorithm.models import Formula


# noinspection PyArgumentList
class TestDTE(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.formula = Formula.objects.get(rule=rule)

        self.backtest = self.formula.start_backtest()
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2015-12-31')
        self.backtest.get_data()
        self.backtest.extra_data()

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'BABA'
        self.hd_args = {

        }
        self.cs_args = {
            'dte': 20,
            'side': 'buy',
            'special': 'standard'
        }

        self.backtest = None
        self.algorithm_analysis('Day to Expire')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        df_hd = self.backtest.handle_data(self.backtest.df_stock)

        print df_hd.to_string(line_width=200)

    def test_create_signal(self):
        """
        Test create signal based on data frame that handle data generate
        """
        df_hd = self.backtest.handle_data(self.backtest.df_stock, **self.hd_args)
        self.cs_args.update({
            'df': self.backtest.df_stock,
            'df_all': self.backtest.df_all
        })

        df_signal = self.backtest.create_signal(**self.cs_args)

        print df_signal.to_string(line_width=200)

        print 'profit: %d' % len(df_signal[df_signal['pct_chg'] > 0])
        print 'loss: %d' % len(df_signal[df_signal['pct_chg'] < 0])
        print 'sum: %.2f%%' % (df_signal['pct_chg'].sum() * 100)

        print df_signal[df_signal['pct_chg'] > 0]['pct_chg'].median()
        print df_signal[df_signal['pct_chg'] > 0]['pct_chg'].mean()

        columns = ('date0', 'date1', 'signal0', 'signal1',
                   'close0', 'close1', 'holding', 'pct_chg')

        for column in columns:
            self.assertIn(column, df_signal.columns)

