import itertools
import numpy as np
import pandas as pd

from base.ufunc import ts
from base.utests import TestUnitSetUp
from research.algorithm.models import Formula


# noinspection PyArgumentList
class TestDTE(TestUnitSetUp):
    def algorithm_analysis(self, rule):
        self.formula = Formula.objects.get(rule=rule)

        self.backtest = self.formula.start_backtest()
        self.backtest.set_symbol_date(self.symbol, '2009-01-01', '2015-12-31')
        self.backtest.convert_data()
        self.backtest.extra_data()

    def setUp(self):
        TestUnitSetUp.setUp(self)

        self.symbol = 'VIX'
        self.hd_args = {

        }
        self.cs_args = {
        }

        self.backtest = None
        self.algorithm_analysis('Day to Expire')

    def test_handle_data(self):
        """
        Test handle data generate new columns base on algorithm
        """
        self.backtest.handle_data(self.backtest.df_stock)

    def test_create_signal(self):
        """
        Test create signal based on data frame that handle data generate
        """
        pass

    def test_stat(self):
        """

        :return:
        """
        #print self.backtest.df_all.head()
        df_stock = self.backtest.df_stock.copy()
        # ts(df_stock)

        df_stock['group'] = pd.qcut(df_stock['close'], 5)
        group = df_stock.group_data('group')

        print group['close'].count()
        print '-' * 70

        print 'below $15:',
        print np.count_nonzero(df_stock['close'] <= 15)
        print 'above $25:',
        print np.count_nonzero(df_stock['close'] >= 25)
        print 'not in 15-25:',
        print np.count_nonzero((df_stock['close'] <= 15) | (df_stock['close'] >= 25))
        print 'between 15-25:',
        print np.count_nonzero((df_stock['close'] > 15) & (df_stock['close'] < 25))


        """
        what do you want to accomplish? goal:
        1 enter vix when price is below 14-11, for butterfly 15-20-25
        1 week before expire, price between 15-25
        """

















