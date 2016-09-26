import numpy as np
import pandas as pd
from django.core.urlresolvers import reverse

from base.utests import TestUnitSetUp
from data.option.day_iv.calc import today_iv
from data.option.day_iv.day_iv import *
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.pyplot as plt


class TestDayImplVol(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'DIS'
        self.full_iv = DayIVCalc(self.symbol)
        self.static = DayImplVolStatic()

    def test_fill_data(self):
        """
        Test fill data all dates
        """
        self.full_iv.get_data()
        df_iv = self.full_iv.calc_iv()

        self.assertTrue(len(df_iv))

        db = pd.HDFStore('test.h5')
        db['iv'] = df_iv
        db.close()

    def test_fill_data_with_one_date(self):
        """
        Test single date fill data
        """
        # date = pd.to_datetime('2015-06-30')
        date = pd.to_datetime('2011-05-09')
        print 'testing date: %s' % date.strftime('%Y-%m-%d')
        self.full_iv.get_data()

        # df_date = self.full_iv.df_all.query('date == %r' % date)
        # df_date = df_date[['date', 'dte', 'mark', 'strike', 'impl_vol']]
        # print df_date.sort_values(['dte', 'strike']).to_string(line_width=1000)

        self.full_iv.df_stock = self.full_iv.df_stock[date:date]
        df_iv = self.full_iv.calc_iv()

        print df_iv

        self.assertTrue(len(df_iv))

    def test_fill_data_with_days_in_dtes(self):
        """
        Test fill data with days exists in dtes
        """
        date = pd.to_datetime('2009-01-15')
        print 'testing date: %s' % date.strftime('%Y-%m-%d')
        self.full_iv.get_data()
        self.full_iv.df_stock = self.full_iv.df_stock[date:date]
        df_iv = self.full_iv.calc_iv()

        print df_iv
        self.assertTrue(len(df_iv))

    def test_fill_data_with_close_in_strikes(self):
        """
        Test fill data with days exists in dtes
        """
        date = pd.to_datetime('2009-03-31')
        print 'testing date: %s' % date.strftime('%Y-%m-%d')
        self.full_iv.get_data()
        self.full_iv.df_stock = self.full_iv.df_stock[date:date]
        df_iv = self.full_iv.calc_iv()

        print df_iv
        self.assertTrue(len(df_iv))

    def test_2d_plot(self):
        """
        Display result in 2d chart
        """
        db = pd.HDFStore('test.h5')
        df_iv = db['iv']
        dates = df_iv[df_iv['dte'] == 30]['date']
        impl_vols = df_iv[df_iv['dte'] == 30]['impl_vol']
        db.close()

        print df_iv.sort_values('impl_vol').head()

        plt.plot(dates, impl_vols)
        plt.xlabel('date')
        plt.ylabel('impl_vols')
        plt.show()

    def test_3d_plot(self):
        """
        Output one date result in 3d view
        """
        db = pd.HDFStore('test.h5')
        df_iv = db['iv']
        db.close()

        date = pd.to_datetime('2015-04-01')
        self.full_iv.get_data()
        df_date0 = self.full_iv.df_all.query('date == %r' % date)
        df_date1 = df_iv.query('date == %r' % date)
        df_date = pd.concat([df_date0, df_date1])
        """:type: pd.DataFrame"""

        x = df_date['dte']
        y = df_date['strike']
        z = df_date['impl_vol']

        fig = plt.figure()
        ax = fig.gca(projection='3d')
        # noinspection PyUnresolvedReferences
        ax.plot_trisurf(x, y, z, cmap=cm.jet, linewidth=0.2)
        # ax.plot_wireframe(x, y, z, rstride=1, cstride=1)
        plt.show()

    def test_start(self):
        """
        Test start to end calc iv then save it
        """
        keys = ('symbol', 'date', 'dte', 'strike', 'dte_iv', 'strike_iv', 'impl_vol')
        symbols = ('AIG', 'C', 'DDD', 'DIS', 'FSLR', 'JPM')
        for symbol in symbols:
            print 'symbol: %s' % symbol.upper()
            calc = DayIVCalc(symbol)
            calc.start()

            db = pd.HDFStore(os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower()))
            df_iv = db.select('/option/day_iv')
            db.close()

            self.assertTrue(len(df_iv))
            for key in keys:
                self.assertIn(key, df_iv.columns)


class TestStrikeNotInDtes2dCalc(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'AIG'
        self.full_iv = DayIVCalc(self.symbol)
        self.static = DayImplVolStatic()
        self.days = 365

    def test_approximation_strike_in_range(self):
        """

        :return:
        """
        self.full_iv.get_data()

        date = pd.to_datetime('2009-01-02')
        dte = 378
        strike = 3.0
        df_date = self.full_iv.df_all.query('date == %r' % date)
        df_date = self.full_iv.format_data(df_date)
        df_dte = df_date.query('dte == %r' % dte)
        # print df_dte.to_string(line_width=1000)

        calc = StrikeNotInDtes2dCalc(strike, dte, df_dte)
        dte_iv = calc.approx()
        self.assertTrue(dte_iv)

    def test_approximation_strike_gt_lt_all(self):
        """

        :return:
        """
        self.full_iv.get_data()

        for strike in (2.5, 36):
            date = pd.to_datetime('2009-01-02')
            dte = 133
            df_date = self.full_iv.df_all.query('date == %r' % date)
            df_date = self.full_iv.format_data(df_date)
            df_dte = df_date.query('dte == %r' % dte)
            print df_dte.to_string(line_width=1000)

            calc = StrikeNotInDtes2dCalc(strike, dte, df_dte)
            dte_iv = calc.approx()
            self.assertTrue(dte_iv)

            print '=' * 70


class TestDayNotInStrikes2dCalc(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'AIG'
        self.full_iv = DayIVCalc(self.symbol)
        self.static = DayImplVolStatic()
        self.days = 365

    def test_approximation_days_in_range(self):
        """

        :return:
        """
        self.full_iv.get_data()

        date = pd.to_datetime('2009-01-02')
        days = 90
        strike = 5
        df_date = self.full_iv.df_all.query('date == %r' % date)
        df_date = self.full_iv.format_data(df_date)
        df_strike = df_date[df_date['strike'] == strike]
        # print df_strike.to_string(line_width=1000)

        calc = DayNotInStrikes2dCalc(days, strike, df_strike)
        strike_iv = calc.approx()
        self.assertTrue(strike_iv)

    def test_approximation_days_gt_lt_all(self):
        """

        :return:
        """
        self.full_iv.get_data()

        date = pd.to_datetime('2009-01-02')
        for days in (13, 800):
            strike = 5
            df_date = self.full_iv.df_all.query('date == %r' % date)
            df_date = self.full_iv.format_data(df_date)
            df_strike = df_date[df_date['strike'] == strike]
            # print df_strike.to_string(line_width=1000)

            calc = DayNotInStrikes2dCalc(days, strike, df_strike)
            strike_iv = calc.approx()
            self.assertTrue(strike_iv)

            print '=' * 70


class TestCalcDayIvView(TestUnitSetUp):
    def test_view(self):
        """
        Test calc day iv view
        """
        symbol = 'NFLX'
        table = 'option'
        path = os.path.join(CLEAN_DIR, '__%s__.h5' % symbol.lower())
        db = pd.HDFStore(path)
        df_valid = db.select('%s/valid/normal' % table)
        df_clean = db.select('%s/clean/normal' % table)
        db.close()

        df_date = df_valid[df_valid['date'] == '2015-08-27']
        df_date = df_date[df_date['name'] == 'CALL'].sort_values('ex_date')
        print df_date.to_string(line_width=1000)

        df_date = df_clean[df_clean['date'] == '2015-08-27']
        df_date = df_date[df_date['name'] == 'CALL'].sort_values('ex_date')
        print df_date.to_string(line_width=1000)

        # self.client.get(reverse('admin:calc_day_iv', kwargs={'symbol': 'GG', 'insert': 0}))


class TestSymbolDateImplVol(TestUnitSetUp):
    def test123(self):
        symbol = 'AIG'
        date = '2016-02-10'
        dtes = [10, 45, 75, 120, 258, 400]

        path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
        db = pd.HDFStore(path)
        df_iv = db.select('option/iv/day')
        db.close()

        for dte in dtes:
            dte_iv = today_iv(df_iv, date, dte)
            print 'dte: %d, iv: %.2f' % (dte, dte_iv)
