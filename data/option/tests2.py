import numpy as np
import pandas as pd
from base.utests import TestUnitSetUp
from data.option.today_iv import TodayIV
from data.option.today_iv2 import *
from rivers.settings import QUOTE, CLEAN


class TestDayImplVol(TestUnitSetUp):
    def setUp(self):
        TestUnitSetUp.setUp(self)
        self.symbol = 'AIG'
        self.day_iv = DayImplVol(self.symbol)
        self.static = DayImplVolStatic()
        self.days = 365

    def test_calc_by_days(self):
        """

        :return:
        """
        """
        self.day_iv.get_data()
        results = self.day_iv.calc_days_by_dtes(self.days)

        df_iv = pd.DataFrame(
            results, columns=['date', 'days', 'linear_iv', 'range_iv', 'poly1d_iv']
        )

        db = pd.HDFStore('test.h5')
        db['iv'] = df_iv
        db.close()

        exit()
        """
        db = pd.HDFStore('test.h5')
        df_iv = db['iv']
        db.close()

        #print len(df_iv)
        #print df_iv.head()

        import matplotlib.pyplot as plt
        #plt.plot(df_iv.index, df_iv['linear_iv'], '-')
        plt.plot(df_iv.index, df_iv['range_iv'], 'b-')
        #plt.plot(df_iv.index, df_iv['poly1d_iv'], 'x-')
        plt.show()


# dte method
class TestDaySingleDte2dCalc(TestDayImplVol):
    def setUp(self):
        """
        Test ExactDte2dCalc for day == dte in df_date
        """
        TestDayImplVol.setUp(self)
        self.day_iv.get_data()
        self.days = 365

        date = pd.to_datetime('2011-06-13')
        self.close = self.day_iv.df_stock.ix[date]['close']
        df_date = self.day_iv.df_all.query('date == %r' % date)
        self.df_date = self.day_iv.format_data(df_date)
        dtes = np.sort(df_date['dte'].unique())
        index = self.static.nearby(dtes, self.days)
        self.df_date = df_date[df_date['dte'] == dtes[index]]
        print 'reduce df_date into single dte...'

    def test_estimate_close_above_below_strikes(self):
        """
        Test calc iv when days in below/above dtes and
        both dtes close is below strikes
        """
        for x in ('>', '<'):
            df_date = self.df_date.query('strike %s %r' % (x, self.close))

            self.calc = DaySingleDte2dCalc(self.close, self.days, df_date)
            linear_iv, range_iv, poly1d_iv = self.calc.estimate()

            self.assertTrue(linear_iv)
            self.assertTrue(range_iv)
            self.assertTrue(poly1d_iv)

            print '=' * 70

    def test_estimate(self):
        """
        Test calc iv when days in below/above dtes and
        both dtes close is below strikes
        """
        self.calc = DaySingleDte2dCalc(self.close, self.days, self.df_date)
        linear_iv, range_iv, poly1d_iv = self.calc.estimate()

        self.assertTrue(linear_iv)
        self.assertTrue(range_iv)
        self.assertTrue(poly1d_iv)


class TestExactDte2dCalc(TestDayImplVol):
    def setUp(self):
        """
        Test ExactDte2dCalc for day == dte in df_date
        """
        TestDayImplVol.setUp(self)

        self.day_iv.get_data()
        self.days = 365
        df_days = self.day_iv.df_all.query('dte == %r' % self.days)
        date = pd.to_datetime(np.sort(df_days['date'].unique())[-1])
        print 'using date: %s' % date.strftime('%Y-%m-%d')
        self.close = self.day_iv.df_stock.ix[date]['close']
        df_date = self.day_iv.df_all.query('date == %r' % date)
        self.df_date = self.day_iv.format_data(df_date)
        print 'close: %.2f, df_date: %d' % (self.close, len(self.df_date))

        self.calc = DayInDte2dCalc

    def test_less_than_2rows(self):
        """
        Test less than 2 rows error raise
        """
        df_error = self.df_date.query('dte == %d' % self.days)[:1]
        print 'df_dte length: %d' % len(df_error)
        self.calc = DayInDte2dCalc(self.close, self.days, df_error)

        self.assertRaises(lambda: self.calc.estimate())
        print 'df_dte less than 2 rows, error raised!'

    def test_exact_close_in_strikes(self):
        """
        Test exact strike found in exact dte, use row impl_vol
        """
        df_dte = self.df_date.query('dte == %d' % self.days)
        strikes = np.array(df_dte['strike'])
        index = self.static.nearby(strikes, self.close)
        close = strikes[index]
        print 'change close: %.2f -> %.2f' % (self.close, close)

        self.calc = DayInDte2dCalc(close, self.days, self.df_date)
        linear_iv, range_iv, poly1d_iv = self.calc.exact_close_in_strikes(df_dte)

        impl_vol = df_dte.query('strike == %r' % close).iloc[0]['impl_vol']
        print 'impl_vol: %.2f, result: %.2f' % (impl_vol, linear_iv)
        self.assertEqual(linear_iv, impl_vol)
        self.assertTrue(linear_iv == range_iv == poly1d_iv)

    def test_close_above_below_strikes(self):
        """
        Test calc iv when close price is above or below all strikes
        """
        df_dte = self.df_date.query('dte == %d' % self.days)
        strikes = np.sort(df_dte['strike'])
        s0, s1 = self.static.two_nearby(strikes, self.close)
        df_above = df_dte.query('strike <= %r' % strikes[s0])
        df_below = df_dte.query('strike >= %r' % strikes[s1])
        print 'strike0: %d(%.2f), strike1: %d(%.2f)' % (s0, strikes[s0], s1, strikes[s1])
        print 'df_above: %d, df_below: %d' % (len(df_above), len(df_below))

        print 'testing close is above all strikes, df_above...'
        self.calc = DayInDte2dCalc(self.close, self.days, df_above)
        linear_iv, range_iv, poly1d_iv = self.calc.close_above_below_strikes('above', df_above)
        self.assertTrue(linear_iv == range_iv == poly1d_iv)

        print '-' * 70

        print 'testing close is below all strikes, df_below...'
        self.calc = DayInDte2dCalc(self.close, self.days, df_above)
        linear_iv, range_iv, poly1d_iv = self.calc.close_above_below_strikes('below', df_below)
        self.assertTrue(linear_iv == range_iv == poly1d_iv)

    def test_close_within_two_strikes(self):
        """
        Testing close price is within two strikes (df_dte only have 2 rows)
        """
        df_dte = self.df_date.query('dte == %d' % self.days)
        strikes = np.sort(df_dte['strike'])
        s0, s1 = self.static.two_nearby(strikes, self.close)
        df_two = df_dte[df_dte['strike'].isin([strikes[s0], strikes[s1]])]

        print 'testing close within two strikes, df_dte (length == 2)...'
        self.calc = DayInDte2dCalc(self.close, self.days, df_two)
        linear_iv, range_iv, poly1d_iv = self.calc.close_within_two_strikes(df_two)
        self.assertTrue(linear_iv == range_iv == poly1d_iv)

    def test_close_within_strike_range(self):
        """
        Test close price is within strikes range
        """
        df_dte = self.df_date.query('dte == %d' % self.days)
        self.calc = DayInDte2dCalc(self.close, self.days, df_dte)
        print 'testing close within strike range...'
        linear_iv, range_iv, poly1d_iv = self.calc.close_within_strike_range(df_dte)

        self.assertTrue(linear_iv)
        self.assertTrue(range_iv)
        self.assertTrue(poly1d_iv)

    def test_all_exact_date(self):
        """
        Test all exact days in df_all
        """
        df_days = self.day_iv.df_all.query('dte == %r' % self.days)
        dates = [pd.to_datetime(d) for d in np.sort(df_days['date'].unique())]

        for date in dates:
            df_date = df_days.query('date == %r' % date)
            df_date = self.day_iv.format_data(df_date)
            print 'date: %s, df_date: %d' % (date.strftime('%Y-%m-%d'), len(df_date))

            calc = DayInDte2dCalc(self.close, self.days, df_date)
            linear_iv, range_iv, poly1d_iv = calc.estimate()

            self.assertTrue(linear_iv)
            self.assertTrue(range_iv)
            self.assertTrue(poly1d_iv)


class TestDayGtLtDtes3dCalc(TestDayImplVol):
    def setUp(self):
        """
        Test ExactDte2dCalc for day == dte in df_date
        """
        TestDayImplVol.setUp(self)
        self.day_iv.get_data()
        self.days = 30

    def test_estimate_both_close_below_strikes(self):
        """
        Test calc iv when days in below/above dtes and
        both dtes close is below strikes
        """
        date = pd.to_datetime('2009-01-14')
        self.close = self.day_iv.df_stock.ix[date]['close']
        df_date = self.day_iv.df_all.query('date == %r' % date)
        self.df_date = self.day_iv.format_data(df_date)

        self.calc = DayGtLtDtes3dCalc(self.close, self.days, self.df_date)
        self.calc.estimate()

    def test_estimate_both_close_in_range_strikes(self):
        """
        Test calc iv when days in below/above dtes and
        both dtes close in range strikes
        """
        date = pd.to_datetime('2010-12-21')
        self.close = self.day_iv.df_stock.ix[date]['close']
        df_date = self.day_iv.df_all.query('date == %r' % date)
        self.df_date = self.day_iv.format_data(df_date)

        self.calc = DayGtLtDtes3dCalc(self.close, self.days, self.df_date)
        self.calc.estimate()

    def test_estimate_dif_close_pos_two_dtes(self):
        """
        Test calc iv when days in below/above dtes and
        one nearby dte close in range; one nearby dte close in above/below
        """
        date = pd.to_datetime('2009-10-19')
        self.close = self.day_iv.df_stock.ix[date]['close']
        df_date = self.day_iv.df_all.query('date == %r' % date)
        self.df_date = self.day_iv.format_data(df_date)

        self.calc = DayGtLtDtes3dCalc(self.close, self.days, self.df_date)
        self.calc.estimate()

    def test_all_gt_lt_dtes(self):
        """
        Test all days is above/below dtes
        """
        for index, data in self.day_iv.df_stock.iterrows():
            close = data['close']
            date = pd.to_datetime(index)
            df_date = self.day_iv.df_all.query('date == %r' % date).sort_values('dte')
            df_date = self.day_iv.format_data(df_date)
            if len(df_date) == 0:
                continue

            dtes = np.array(df_date['dte'].unique())
            d0, d1 = self.static.two_nearby(dtes, self.days)
            if not dtes[d0] <= self.days <= dtes[d1]:
                print 'testing date: %s' % date.strftime('%Y-%m-%d')
                self.calc = DayGtLtDtes3dCalc(close, self.days, df_date)
                self.calc.estimate()

                print '=' * 70


class TestDayInRangeDtes3dCalc(TestDayImplVol):
    def setUp(self):
        """
        Test ExactDte2dCalc for day == dte in df_date
        """
        TestDayImplVol.setUp(self)
        self.day_iv.get_data()
        self.days = 150

    def test_estimate_days_in_exact_two_dtes(self):
        """
        Test calc iv when days in below/above dtes and
        both dtes close is below strikes
        """
        date = pd.to_datetime('2011-06-13')
        self.close = self.day_iv.df_stock.ix[date]['close']
        df_date = self.day_iv.df_all.query('date == %r' % date)
        self.df_date = self.day_iv.format_data(df_date)
        dtes = np.sort(df_date['dte'].unique())
        i0, i1 = self.static.two_nearby(dtes, self.days)
        df_date = df_date[df_date['dte'].isin([dtes[i0], dtes[i1]])]
        self.calc = DayInRangeDtes3dCalc(self.close, self.days, df_date)
        self.calc.estimate()

    def test_estimate_days_in_exact_four_dtes(self):
        """
        Test calc iv when days in below/above dtes and
        both dtes close is below strikes
        """
        date = pd.to_datetime('2011-06-13')
        self.close = self.day_iv.df_stock.ix[date]['close']
        df_date = self.day_iv.df_all.query('date == %r' % date)
        self.df_date = self.day_iv.format_data(df_date)
        self.calc = DayInRangeDtes3dCalc(self.close, self.days, self.df_date)
        self.calc.estimate()

    def test_all_days_in_range_dtes(self):
        """
        Test all days is above/below dtes
        """
        for index, data in self.day_iv.df_stock.iterrows():
            close = data['close']
            date = pd.to_datetime(index)
            df_date = self.day_iv.df_all.query('date == %r' % date).sort_values('dte')
            df_date = self.day_iv.format_data(df_date)
            if len(df_date) == 0:
                continue

            dtes = np.sort(df_date['dte'].unique())
            i0, i1 = self.static.two_nearby(dtes, self.days)

            if dtes[i0] < self.days < dtes[i1]:
                self.calc = DayInRangeDtes3dCalc(close, self.days, df_date)
                self.calc.estimate()
                print '=' * 70


# strike method
class TestExactStrike2dCalc(TestDayImplVol):
    def setUp(self):
        """
        Test ExactDte2dCalc for day == dte in df_date
        """
        TestDayImplVol.setUp(self)

        self.day_iv.get_data()
        date = pd.to_datetime('2015-05-05')
        print 'using date: %s' % date.strftime('%Y-%m-%d')
        self.close = self.day_iv.df_stock.ix[date]['close']
        df_date = self.day_iv.df_all.query('date == %r' % date)
        self.df_date = self.day_iv.format_data(df_date)
        self.days = 30
        self.calc = ExactStrike2dCalc
        print 'close: %.2f, days: %d, df_date: %d' % (self.close, self.days, len(self.df_date))

    def test_days_within_two_dtes(self):
        """
        Test exact close strike within 2 dtes (df_strike == 2)
        """
        df_strike = self.df_date.query('strike == %r' % self.close).sort_values('dte')
        dtes = np.array(df_strike['dte'])
        impl_vols = np.array(df_strike['impl_vol'])
        d0, d1, dtes, impl_vols = self.static.reduce_samples(self.days, dtes, impl_vols)
        df_strike = df_strike[df_strike['dte'].isin([dtes[d0], dtes[d1]])]
        print 'reduce sample size to df_strikes: %d' % len(df_strike)
        calc = ExactStrike2dCalc(self.close, self.days, self.df_date)
        linear_iv, range_iv, poly1d_iv = calc.days_within_two_dtes(df_strike)

        self.assertTrue(linear_iv == range_iv == poly1d_iv)

    def test_days_within_range_dtes(self):
        """
        Test exact close strike within range dtes (df_strike > 2)
        """
        df_strike = self.df_date.query('strike == %r' % self.close)
        print 'df_strikes: %d' % len(df_strike)
        calc = ExactStrike2dCalc(self.close, self.days, self.df_date)
        linear_iv, range_iv, poly1d_iv = calc.days_within_range_dtes(df_strike)

        self.assertTrue(linear_iv)
        self.assertTrue(range_iv)
        self.assertTrue(poly1d_iv)

    def test_all(self):
        """
        Test all exact close price strike in df_all
        """
        # get strike exists in range cycle data
        dates = []
        for index, data in self.day_iv.df_stock.iterrows():
            date = pd.to_datetime(index)
            df_strike = self.day_iv.df_all.query('date == %r & strike == %r' % (
                date, data['close']
            ))

            if len(df_strike) > 1:
                print 'close: %.2f, df_strike: %d' % (data['close'], len(df_strike))
                df_strike = df_strike.sort_values('dte')
                dtes = np.array(df_strike['dte'])
                d0, d1 = self.static.two_nearby(dtes, self.days)
                df_dte = df_strike[df_strike['dte'].isin([dtes[d0], dtes[d1]])]
                count = df_dte['strike'].value_counts()

                if count[data['close']] == 2:
                    print 'date: %s, strike range: %d' % (
                        date.strftime('%Y-%m-%d'), count[data['close']]
                    )
                    dates.append(date)
                else:
                    print 'skip...'

                print '-' * 70

        # start testing
        print '=' * 70
        print 'start testing...'
        for date in dates:
            close = self.day_iv.df_stock.ix[date]['close']
            df_date = self.day_iv.df_all.query('date == %r' % date)

            calc = ExactStrike2dCalc(close, self.days, df_date)
            linear_iv, range_iv, poly1d_iv = calc.estimate()

            self.assertTrue(linear_iv)
            self.assertTrue(range_iv)
            self.assertTrue(poly1d_iv)


# todo: later
class TestCloseGtLtStrikes3dCalc(TestDayImplVol):
    def setUp(self):
        """
        Test ExactDte2dCalc for day == dte in df_date
        """
        TestDayImplVol.setUp(self)

        self.day_iv.get_data()
        self.days = 30

    def test_strikes_in_range_dtes(self):
        """
        :return:
        """
        date = pd.to_datetime('2009-06-03')  # lower
        self.close = self.day_iv.df_stock.ix[date]['close']
        for close in (self.close, 100):
            print 'using close: %2.f, date: %s' % (close, date.strftime('%Y-%m-%d'))

            df_date = self.day_iv.df_all.query('date == %r' % date)
            self.df_date = self.day_iv.format_data(df_date)

            print 'close: %.2f, days: %d, df_date: %d' % (close, self.days, len(self.df_date))

            self.calc = CloseGtLtStrikes3dCalc(close, self.days, self.df_date)
            self.calc.estimate()

            # todo: max

    def test_strikes_in_range_with_gt_2dtes(self):
        """

        :return:
        """

        date = pd.to_datetime('2015-03-18')  # lower
        print 'using close: %2.f, date: %s' % (self.close, date.strftime('%Y-%m-%d'))
        self.close = self.day_iv.df_stock.ix[date]['close']
        df_date = self.day_iv.df_all.query('date == %r' % date)
        self.df_date = self.day_iv.format_data(df_date)
        self.calc = CloseGtLtStrikes3dCalc
        print 'close: %.2f, days: %d, df_date: %d' % (self.close, self.days, len(self.df_date))

        self.calc = CloseGtLtStrikes3dCalc(self.close, self.days, self.df_date)
        self.calc.strikes_in_range_with_gt_2dtes(self.df_date)


    def test_all(self):
        """

        :return:
        """
        for index, data in self.day_iv.df_stock.iterrows():
            date = pd.to_datetime(index)
            close = data['close']
            df_date = self.day_iv.df_all.query('date == %r' % date).sort_values('dte')
            dtes = np.array(df_date['dte'].unique())
            d0, d1 = self.static.two_nearby(dtes, self.days)
            if d0 == d1 or len(dtes) < 2 or len(df_date) < 2:  # no range dtes, use days gt/lt dtes
                continue

            df_dte = df_date[df_date['dte'].isin([dtes[d0], dtes[d1]])]
            s0, s1 = df_dte['strike'].min(), df_dte['strike'].max()

            if close < s0 or close > s1:  # max, min for both range dtes
                print 'close: %.2f, date: %s, df_date: %d' % (
                    close, date.strftime('%Y-%m-%d'), len(df_date)
                )
                print 'min strike: %.2f, max strike: %.2f' % (s0, s1)
                print '-' * 70

        print '=' * 70



