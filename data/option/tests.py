import numpy as np
import pandas as pd
from base.utests import TestUnitSetUp
from data.option.today_iv import TodayIV
from rivers.settings import QUOTE, CLEAN


class TestSingleCallCS(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'AIG'
        self.days = 365
        db = pd.HDFStore(QUOTE)
        self.df_stock = db.select('stock/thinkback/%s' % self.symbol.lower())
        db.close()

        db = pd.HDFStore(CLEAN)
        df_normal = db.select('iv/%s/clean/normal' % self.symbol.lower())
        path = '/iv/%s/clean/split/old' % self.symbol.lower()
        if path in db.keys():
            df_split0 = db.select(path)
            self.df_all = pd.concat([df_normal, df_split0])
            """:type: pd.DataFrame"""
        else:
            self.df_all = df_normal
        db.close()

        self.today_iv = TodayIV(self.symbol)
        self.today_iv.df_stock = self.df_stock['20090101':'20150630']
        self.today_iv.df_all = self.df_all
        self.date = pd.to_datetime('20150625')

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

    def test_format_data(self):
        """
        Test remove duplicate ('dte', 'strike') split data in DataFrame
        """
        date = pd.to_datetime('2009-04-16')
        df_date0 = self.df_all.query('date == %r & name == "CALL"' % date)
        print df_date0.to_string(line_width=1000)
        df_date1 = self.today_iv.format_data(df_date0)
        print df_date1.to_string(line_width=1000)

        self.assertGreater(len(df_date0), len(df_date1))

    def test_nearby_365days(self):
        """
        Test calc using exists nearby 365-days in dte cycles
        """
        date = pd.to_datetime('2012-10-17')
        dte = 364
        close = self.df_stock.ix[date]['close']
        df_date = self.df_all.query('date == %r & name =="CALL"' % date)

        range_iv, poly1d_iv, linear_iv = self.today_iv.nearby_365days(close, dte, df_date)

        self.assertEqual(type(range_iv), float)
        self.assertEqual(type(poly1d_iv), float)
        self.assertEqual(type(linear_iv), float)
        self.assertAlmostEqual(poly1d_iv / 100.0, linear_iv / 100.0, 0)

    def test_nearby_strike(self):
        """
        Test calc iv using nearby strike exists in dataframe
        """
        date = pd.to_datetime('2009-01-14')
        close = self.df_stock.ix[date]['close']
        df_date = self.df_all.query('date == %r & name == "CALL"' % date)
        df_date = self.today_iv.format_data(df_date)
        print '-' * 70

        range_iv, poly1d_iv, linear_iv = self.today_iv.nearby_strike(close, self.days, df_date)
        print range_iv, poly1d_iv, linear_iv

        self.assertEqual(type(range_iv), float)
        self.assertEqual(type(poly1d_iv), float)
        self.assertEqual(type(linear_iv), float)
        self.assertAlmostEqual(poly1d_iv / 100.0, linear_iv / 100.0, 0)

    def test_single_nearby_strike(self):
        """
        Test single nearby strike found on all cycles
        2009-01-14
        """
        date = pd.to_datetime('2009-04-24')
        close = self.df_stock.ix[date]['close']
        df_date = self.df_all.query('date == %r & name == "CALL"' % date)
        df_date = self.today_iv.format_data(df_date)
        # print df_date.to_string(line_width=1000)

        range_iv, linear_iv = self.today_iv.price_not_in_strike_range(close, self.days, df_date)
        self.assertEqual(type(range_iv), float)
        self.assertEqual(type(linear_iv), float)
        self.assertAlmostEqual(range_iv / 100.0, linear_iv / 100.0, 0)

    def test_single_nearby_cycle(self):
        """
        Test single nearby cycle found for 365-days
        """
        date = pd.to_datetime('2011-05-23')
        close = self.df_stock.ix[date]['close']
        df_date = self.df_all.query('date == %r & name == "CALL"' % date)
        # print df_date.to_string(line_width=1000)
        df_date = self.today_iv.format_data(df_date)
        # print df_date.to_string(line_width=1000)

        range_iv, linear_iv = self.today_iv.single_nearby_cycle(close, self.days, df_date)
        self.assertEqual(type(range_iv), float)
        self.assertEqual(type(linear_iv), float)
        self.assertAlmostEqual(range_iv / 100.0, linear_iv / 100.0, 0)

    def test_calc_cycles(self):
        """
        Test calculate iv using cycle method
        """
        date = pd.to_datetime('2009-04-16')
        close = self.df_stock.ix[date]['close']
        days = 30
        df_date = self.df_all.query('date == %r & name == "CALL"' % date)
        df_date = self.today_iv.format_data(df_date)

        range_iv, poly1d_iv, linear_iv = self.today_iv.multi_cycles_3d(close, days, df_date)

        self.assertEqual(type(range_iv), float)
        self.assertEqual(type(poly1d_iv), float)
        self.assertEqual(type(linear_iv), float)
        self.assertAlmostEqual(range_iv / 100.0, linear_iv / 100.0, 0)

    def test_calc_strike(self):
        """
        Test calculate iv using strike method, new version
        """
        date = pd.to_datetime('2011-05-23')
        close = self.df_stock.ix[date]['close']
        days = 30
        df_date = self.df_all.query(
            'date == %r & name == "CALL" & others == ""' % date
        )
        df_date = self.today_iv.format_data(df_date)

        range_iv, poly1d_iv, linear_iv = self.today_iv.multi_strikes_3d(close, days, df_date)

        self.assertEqual(type(range_iv), float)
        self.assertEqual(type(poly1d_iv), float)
        self.assertEqual(type(linear_iv), float)
        self.assertAlmostEqual(range_iv / 100.0, linear_iv / 100.0, 0)
        self.assertAlmostEqual(poly1d_iv / 100.0, linear_iv / 100.0, 0)

    def test_calc(self):
        """

        :return:
        """
        symbol = 'AIG'
        day = 365
        today_iv = TodayIV(symbol)
        today_iv.get_data()
        results = today_iv.calc_by_days(day)
        self.assertGreater(len(results), 0)

    def test_diff_symbols_days(self):
        """
        Test different symbols and days for calc
        """
        symbols = ['AIG', 'C', 'DDD', 'EBAY', 'FSLR', 'HD', 'JPM', 'WFC']
        days = [30, 60, 90, 150, 365]

        f = open(r'D:/rivers/debug.txt', mode='a')
        for symbol in symbols:
            today_iv = TodayIV(symbol)
            for day in days:
                f.writelines('<%s> %s start\n' % (symbol, day))
                today_iv.start(day)
                f.writelines('<%s> %s end\n' % (symbol, day))
                print '.' * 40
                #break
            print '-' * 70
            #break
        f.close()

        # todo: 2009-04-24, c, 60 days, negative impl_vol

    def test123(self):
        # self.symbol = 'EBAY'
        db = pd.HDFStore(QUOTE)
        df_vol = db.select('option/%s/final/today_iv' % self.symbol.lower())
        df_vol365 = df_vol.query('days == 365')
        df_vol30 = df_vol.query('days == 30')
        db.close()

        import matplotlib.pyplot as plt
        df_vol30 = df_vol365
        df_vol30 = df_vol30.set_index('date')
        df_vol30 = df_vol30.ix['20090101':'20091231']

        plt.plot(df_vol30.index, df_vol30['linear_iv'], '-')
        #plt.plot(df_vol365['date'], df_vol365['range_iv'], '-')
        plt.show()

        """
        df_join = pd.merge(df_vol30, df_vol365, on='date')

        print df_join.query('date < %r' % '20100101').to_string(line_width=1000)

        self.assertFalse(np.count_nonzero(np.isnan(df_vol30['range_iv'])))
        self.assertFalse(np.count_nonzero(np.isnan(df_vol30['linear_iv'])))
        self.assertFalse(np.count_nonzero(np.isnan(df_vol30['poly1d_iv'])))
        """


        # AIG160115C48, 2015-06-30, wrong bid-ask










































