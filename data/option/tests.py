import numpy as np
import pandas as pd
from base.utests import TestUnitSetUp
from data.option.today_iv import TodayIV
from rivers.settings import QUOTE, CLEAN


class TestSingleCallCS(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'AIG'
        db = pd.HDFStore(QUOTE)
        self.df_stock = db.select('stock/thinkback/%s' % self.symbol.lower())
        db.close()

        db = pd.HDFStore(CLEAN)
        df_normal = db.select('iv/%s/clean/normal' % self.symbol.lower())
        df_split0 = db.select('iv/%s/clean/split/old' % self.symbol.lower())
        db.close()
        self.df_all = pd.concat([df_normal, df_split0])
        """:type: pd.DataFrame"""

        self.today_iv = TodayIV(self.symbol)
        self.today_iv.df_stock = self.df_stock
        self.today_iv.df_all = self.df_all
        self.date = pd.to_datetime('20150625')
        """
        20150630 - 22.98
        20150629 - 22.97
        20150626 - 19.41
        20150625 - 19.03
        """

    def test_range_expr(self):
        """
        Test range expression using at least 3 items data
        """
        x = [49.0, 133.0, 378.0, 749.0]
        y = [109.02, 109.98, 101.17, 105.49]

        skip = [(0, 0), (1, 0), (0, -1)]
        for i, j in skip:
            print 'range: %d:%d' % (0 + i, len(x) + j)
            a = x[0 + i:len(x) + j]
            b = y[0 + i:len(x) + j]
            print 'x:', a
            print 'y:', b

            range_iv = self.today_iv.range_expr(a, b, 365)
            print 'range_iv: %.2f' % range_iv
            self.assertTrue(y[1] > range_iv > y[2])
            print '-' * 70

    def test_remove_split(self):
        """
        Test remove duplicate ('dte', 'strike') split data in DataFrame
        """
        date = pd.to_datetime('2009-09-04')
        print 'date: %s' % date.strftime('%Y-%m-%d')

        df_date0 = self.df_all.query('date == %r & name == "CALL"' % date)
        df_date1 = self.today_iv.remove_split(df_date0)
        print df_date1.sort_values('dte').to_string(line_width=1000)

        self.assertGreater(len(df_date0), len(df_date1))

    def test_nearby_365days(self):
        """
        Test calc using exists nearby 365-days in dte cycles
        """
        date = pd.to_datetime('2010-01-21')
        print 'date: %s' % date.strftime('%Y-%m-%d')
        close = self.df_stock.ix[date]['close']
        df_date = self.df_all.query('date == %r & name =="CALL"' % date)

        range_iv, poly1d_iv, linear_iv = self.today_iv.nearby_365days(close, 365, df_date)
        print 'poly1d_iv: %.2f, linear_iv: %.2f' % (poly1d_iv, linear_iv)

        self.assertEqual(type(range_iv), float)
        self.assertEqual(type(poly1d_iv), float)
        self.assertEqual(type(linear_iv), float)
        self.assertAlmostEqual(poly1d_iv / 100.0, linear_iv / 100.0, 0)

    def test_nearby_strike(self):
        """
        Test calc iv using nearby strike exists in dataframe
        """
        date = pd.to_datetime('2009-09-04')
        print 'date: %s' % date.strftime('%Y-%m-%d')

        df_date = self.df_all.query('date == %r & name == "CALL"' % date)
        df_date = self.today_iv.remove_split(df_date)
        range_iv, poly1d_iv, linear_iv = self.today_iv.nearby_strike(date, df_date, False)

        self.assertEqual(type(range_iv), float)
        self.assertEqual(type(poly1d_iv), float)
        self.assertEqual(type(linear_iv), float)
        self.assertAlmostEqual(poly1d_iv / 100.0, linear_iv / 100.0, 0)

    def test_single_nearby_strike(self):
        """
        Test single nearby strike found on all cycles
        """
        date = pd.to_datetime('2009-01-02')
        close = self.df_stock.ix[date]['close']
        df_date = self.df_all.query('date == %r & name == "CALL" & right == "100"' % date)

        range_iv, linear_iv = self.today_iv.single_nearby_strike(close, df_date, True)
        self.assertEqual(type(range_iv), float)
        self.assertEqual(type(linear_iv), float)
        self.assertAlmostEqual(range_iv / 100.0, linear_iv / 100.0, 0)

    def test_single_nearby_cycle(self):
        """
        Test single nearby cycle found for 365-days
        """
        date = pd.to_datetime('2010-01-22')
        close = self.df_stock.ix[date]['close']
        df_date = self.df_all.query('date == %r & name == "CALL"' % date)
        df_date = df_date.query('dte < 365')
        dtes = np.sort(np.array(df_date['dte'].unique()))
        d0, d1 = self.today_iv.two_nearby(dtes, 365)
        print 'i0: %d, dte0: %d, i1: %d, dte1: %d' % (d0, dtes[d0], d1, dtes[d1])

        range_iv, linear_iv = self.today_iv.single_nearby_cycle(close, df_date, False)
        self.assertEqual(type(range_iv), float)
        self.assertEqual(type(linear_iv), float)
        self.assertAlmostEqual(range_iv / 100.0, linear_iv / 100.0, 0)

    def test_calc_cycles(self):
        """
        Test calculate iv using cycle method
        """
        poly1d_iv, linear_iv = self.today_iv.calc_cycles(date=self.date, plot=False)

        self.assertEqual(type(poly1d_iv), float)
        self.assertEqual(type(linear_iv), float)
        self.assertAlmostEqual(poly1d_iv / 100.0, linear_iv / 100.0, 0)

    def test_calc_strike(self):
        """
        Test calculate iv using strike method
        """
        self.today_iv.calc_strikes(date=self.date, plot=False)
        poly1d_iv, linear_iv = self.today_iv.calc_strikes(date=self.date)

        self.assertEqual(type(poly1d_iv), float)
        self.assertEqual(type(linear_iv), float)
        self.assertAlmostEqual(poly1d_iv / 100.0, linear_iv / 100.0, 0)

    def test_calc_iv(self):
        """
        Test calculate iv using strike method
        """
        self.today_iv.calc_iv(date=self.date)





    def test_calc(self):
        """

        :return:
        """
        self.today_iv.calc()
























