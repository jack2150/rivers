import pandas as pd
from base.tests import TestSetUp
from research.algorithm.formula.event.earning.merge import merge_stock_earning
from rivers.settings import QUOTE_DIR


class TestMergeStockEarning(TestSetUp):
    def setUp(self):
        TestSetUp.setUp(self)

        self.symbol = 'AIG'

        db = pd.HDFStore(QUOTE_DIR)
        self.df_stock = db.select('stock/google/%s' % self.symbol.lower())
        self.df_stock = self.df_stock.reset_index()
        self.df_earning = db.select('event/earning/%s' % self.symbol.lower())
        db.close()

    def test_merge_stock_earning(self):
        """

        :return:
        """
        df_merge = merge_stock_earning(self.df_stock, self.df_earning)

        self.assertEqual(type(df_merge), pd.DataFrame)
        self.assertTrue(len(df_merge))
        self.assertGreater(
            len(df_merge[df_merge['actual_date'].isnull()]),  # not earning
            len(df_merge[~df_merge['actual_date'].isnull()])  # is earning
        )

        print df_merge[~df_merge['actual_date'].isnull()].to_string(line_width=1000)
