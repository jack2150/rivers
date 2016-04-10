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
        self.df_contract = db.select('option/%s/final/contract' % self.symbol.lower())
        self.df_option = db.select('option/%s/final/data' % self.symbol.lower())
        self.df_all = pd.merge(self.df_option, self.df_contract, on='option_code')
        db.close()

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

    def test_exists_365days(self):
        """

        :return:
        """
        date = pd.to_datetime(self.df_all.query('dte == 365')['date'].unique()[-1])
        print 'date: %s' % date.strftime('%Y-%m-%d')

        poly1d_iv, linear_iv = self.today_iv.exists_365days(date=date, plot=False)
        print 'poly1d_iv: %.2f, linear_iv: %.2f' % (poly1d_iv, linear_iv)

        self.assertEqual(type(poly1d_iv), float)
        self.assertEqual(type(linear_iv), float)
        self.assertAlmostEqual(poly1d_iv / 100.0, linear_iv / 100.0, 0)

    def test_remove_split(self):
        """

        :return:
        """
        date = pd.to_datetime('2009-09-04')
        print 'date: %s' % date.strftime('%Y-%m-%d')

        df_date0 = self.df_all.query('date == %r & name == "CALL"' % date)
        df_date1 = self.today_iv.remove_split(df_date0)

        self.assertGreater(len(df_date0), len(df_date1))

    def test_exists_close_strike(self):
        """

        :return:
        """
        date = pd.to_datetime('2009-09-04')
        print 'date: %s' % date.strftime('%Y-%m-%d')

        df_date = self.df_all.query('date == %r & name == "CALL"' % date)
        #print df_date.to_string(line_width=1000)

        # todo: 504-days missing in data???

        df_date = self.today_iv.remove_split(df_date)
        self.today_iv.exists_close_strike(date, df_date, False)


        """
        db = pd.HDFStore(CLEAN)
        df_normal = db.select('iv/%s/clean/normal' % self.symbol.lower())
        df_split0 = db.select('iv/%s/clean/split/old' % self.symbol.lower())
        db.close()

        df_option = pd.concat([df_normal, df_split0])
        df_temp = df_option.query('date == %r & name == "CALL"' % date).sort_values('dte')
        print df_temp.to_string(line_width=1000)
        #print df_temp['dte'].unique()

        df_all = self.df_all.query('date == %r & name == "CALL"' % date).sort_values('dte')
        print df_all.to_string(line_width=1000)
        """

        # todo: you clean everyday without merging data, using

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

    def test_no_duplicated_strike(self):
        """

        :return:
        """
        dates = [pd.to_datetime('2009-06-23'), pd.to_datetime('2009-01-02')]
        for date in dates[1:]:
            close = self.df_stock.ix[date]['close']

            df_date = self.df_all.query('date == %r & name == "CALL"' % date)
            dtes = np.sort(np.array(df_date['dte'].unique()))
            d0, d1 = self.today_iv.two_nearby(dtes, 365)
            df_near = df_date.query('dte == %r | dte == %r' % (dtes[d0], dtes[d1]))

            self.today_iv.no_duplicated_strike(close, df_near)

    def test_single_nearby_cycle(self):
        """

        :return:
        """
        date = pd.to_datetime('2010-01-22')
        close = self.df_stock.ix[date]['close']
        df_date = self.df_all.query('date == %r & name == "CALL"' % date)
        dtes = np.sort(np.array(df_date['dte'].unique()))
        d0, d1 = self.today_iv.two_nearby(dtes, 365)
        print 'i0: %d, dte0: %d, i1: %d, dte1: %d' % (d0, dtes[d0], d1, dtes[d1])

        if d0 == d1:
            self.today_iv.single_nearby_cycle(close, df_date, False)



    def test_calc(self):
        """

        :return:
        """
        self.today_iv.calc()
























