import numpy as np
import pandas as pd
from rivers.settings import QUOTE, CLEAN

output = '%-6s | %-s'


class DayImplVol(object):
    def __init__(self, symbol):
        self.symbol = symbol.lower()
        self.df_stock = pd.DataFrame()
        self.df_all = pd.DataFrame()
        self.static = DayImplVolStatic()

    def get_data(self):
        """
        Get data from hdf5 db
        """
        print output % ('DATA', 'symbol: %s' % self.symbol.upper())
        db = pd.HDFStore(QUOTE)
        self.df_stock = db.select('stock/thinkback/%s' % self.symbol.lower())
        # df_contract = db.select('option/%s/final/contract' % self.symbol.lower())
        # df_option = db.select('option/%s/final/data' % self.symbol.lower())
        # self.df_all = pd.merge(df_option, df_contract, on='option_code')
        db.close()

        db = pd.HDFStore(CLEAN)
        df_normal = db.select('iv/%s/clean/normal' % self.symbol.lower())
        df_split0 = db.select('iv/%s/clean/split/old' % self.symbol.lower())
        db.close()
        self.df_all = pd.concat([df_normal, df_split0])
        """:type: pd.DataFrame"""
        self.df_all = self.df_all.query('name == "CALL"')  # only call
        print output % ('DATA', 'df_normal: %d, df_split0: %d' % (len(df_normal), len(df_split0)))
        print output % ('DATA', 'df_stock: %d, df_all: %d' % (len(self.df_stock), len(self.df_all)))
        print '-' * 70

    @staticmethod
    def format_data(df_date):
        """
        Format data remove zero impl_vol and others
        Remove duplicate split data
        :param df_date: pd.DataFrame
        :return: pd.DataFrame
        """
        # remove 0 impl_vol and 0 days
        df_date = df_date.query('name == "CALL" & impl_vol > 0 & others == ""').copy()
        if len(df_date) == 0:
            return df_date

        df_date['match'] = df_date.apply(lambda x: '%s_%s' % (x['dte'], x['strike']), axis=1)
        # print df_date.sort_values(['dte', 'strike']).to_string(line_width=1000)

        # remove split
        rights = df_date['right'].unique()
        if len(rights) > 1:
            print output % ('SPLIT', 'rights: %s' % list(rights))
            df_split = df_date.query('right != "100"')
            """:type: pd.DataFrame"""
            df_normal = df_date.query('right == "100"')
            if len(df_normal) and len(df_split):
                length0 = len(df_date)

                print output % ('SPLIT', 'remove duplicate split/normal rows')
                df_split = df_split[~df_split['match'].isin(df_normal['match'])]
                df_date = pd.concat([df_normal, df_split])
                """:type: pd.DataFrame"""

                length1 = len(df_date)
                print output % ('DATA', 'df_date0: %d, df_date1: %d' % (length0, length1))
                print '-' * 70

        del df_date['match']
        # print df_date.sort_values(['dte', 'strike']).to_string(line_width=1000)

        # remove dte that only have 1 row
        dtes = df_date['dte'].value_counts()
        df_date = df_date[~df_date['dte'].isin(dtes[dtes == 1].index)]

        return df_date.copy()

    def calc_days_by_dtes(self, days):
        """
        Calc iv using dte frame by frame method
        :param days: int
        :return: list
        """
        results = []
        for date, data in self.df_stock.iterrows():
            close = data['close']
            date = pd.to_datetime(date)
            df_date = self.df_all.query('date == %r' % date)
            df_date = self.format_data(df_date)
            """:type: pd.DataFrame"""
            print output % ('INIT', 'date: %s, close: %.2f, df_date: %d' % (
                date.strftime('%Y-%m-%d'), close, len(df_date)
            ))
            print '-' * 70

            if len(df_date) == 0:
                print output % ('ERROR', 'no enough data...')
                print '=' * 70
                continue

            dtes = list(np.sort(df_date['dte'].unique()))

            if len(dtes) == 1:  # single dte only
                calc = DaySingleDte2dCalc(close, days, df_date)
                linear_iv, range_iv, poly1d_iv = calc.estimate()
                results.append((date, days, linear_iv, range_iv, poly1d_iv))
                print '=' * 70
                continue

            if days in dtes:  # exact day in dtes
                calc = DayInDte2dCalc(close, days, df_date)
                linear_iv, range_iv, poly1d_iv = calc.estimate()
                results.append((date, days, linear_iv, range_iv, poly1d_iv))
                print '=' * 70
                continue

            d0, d1 = self.static.two_nearby(dtes, days)
            if not dtes[d0] <= days <= dtes[d1]:  # single nearby dtes
                calc = DayGtLtDtes3dCalc(close, days, df_date)
                linear_iv, range_iv, poly1d_iv = calc.estimate()
                results.append((date, days, linear_iv, range_iv, poly1d_iv))
                print '=' * 70
                continue

            # 3d cycle by cycle calc
            calc = DayInRangeDtes3dCalc(close, days, df_date)
            linear_iv, range_iv, poly1d_iv = calc.estimate()
            results.append((date, days, linear_iv, range_iv, poly1d_iv))
            print '=' * 70

        return results


class DayImplVolStatic(object):
    @staticmethod
    def list_index(data, index0, index1, value):
        """
        Calculate the list index range that to be use
        :param data: list
        :param index0: int
        :param index1: int
        :param value: int
        :return: int, int
        """
        i0 = index0 - value if index0 - value > -1 else 0
        i1 = index1 + value + 1 if index1 + value + 1 <= len(data) else len(data)
        return i0, i1

    @staticmethod
    def nearby(data, value, second=False):
        """
        Get the most nearby value in a list
        :param data:
        :param value:
        :param second:
        :return: int
        """
        temp0 = np.array(data)
        temp1 = np.abs(temp0 - value)
        if second:
            index0 = list(temp1).index(np.amin(temp1))
            if temp0[index0] < value:
                index = index0 + 1 if index0 + 1 < len(temp0) else len(temp0) - 1
            else:
                index = index0 - 1 if index0 - 1 > -1 else 0
        else:
            index = list(temp1).index(np.amin(temp1))

        return index

    def two_nearby(self, data, value):
        """
        Get the most nearby two values in a list
        :param data: list
        :param value: float or int
        :return: int, int
        """
        a = self.nearby(data, value)
        b = self.nearby(data, value, True)
        a, b = sorted([a, b])

        if a == b:
            if a == b == 0:
                b += 1
            elif a == b == len(data) - 1:
                b -= 1
            else:
                raise ValueError('Invalid 2 nearby indexes: %d(%.2f), %d(%.2f)' % (
                    a, b, data[a], data[b]
                ))

        return a, b

    @staticmethod
    def linear_expr(x0, x1, y0, y1, base):
        """
        Linear iv expression
        :param x0: float
        :param x1: float
        :param y0: float
        :param y1: float
        :param base: float
        :return: float
        """
        if y0 == y1:
            result = y0
        else:
            result = round(y0 + ((y1 - y0) / (x1 - x0) * (base - x0)), 2)

        return result

    def range_expr(self, x, y, base):
        """
        Triple linear range estimate using median
        :param x: list
        :param y: list
        :param base: float/int
        :return: float
        """
        if not len(x) == len(y) >= 3:
            if len(x) == len(y) == 1:
                return y[0]
            elif len(x) == len(y) == 2:
                return self.linear_expr(x[0], x[1], y[0], y[1], base)
            else:
                raise ValueError('Range expr x, y list is empty')

        for a, b in zip(x, y):
            print output % ('DATA', 'calc range, dte/strike: %.2f, impl_vol: %.2f' % (a, b))

        if len(x) == len(y) == 3:
            d0, d1 = self.two_nearby(x, base)
            if d0 == 1 and d1 == 2:
                iv0 = y[1] + (y[1] - y[0]) / (x[1] - x[0]) * (base - x[1])
                iv1 = self.linear_expr(x[1], x[2], y[1], y[2], base)
                results = [iv0, iv1]
                i0, i1 = 1, 2
            else:
                iv1 = self.linear_expr(x[0], x[1], y[0], y[1], base)
                iv2 = y[1] - (y[2] - y[1]) / (x[2] - x[1]) * (x[1] - base)
                results = [iv1, iv2]
                i0, i1 = 0, 1
        else:
            iv0 = y[1] + (y[1] - y[0]) / (x[1] - x[0]) * (base - x[1])
            iv1 = self.linear_expr(x[1], x[2], y[1], y[2], base)
            iv2 = y[2] - (y[3] - y[2]) / (x[3] - x[2]) * (x[2] - base)
            results = [iv0, iv1, iv2]
            i0, i1 = 1, 2

        print output % ('NEAR', 'index0: %d, index1: %d' % (i0, i1))
        print output % ('CALC', 'range_ivs: %s' % [round(r, 2) for r in results])

        if len(results) == 1:
            result = results[0]
        else:
            result = np.mean(results)
            if not (y[i0] <= result <= y[i1] or y[i0] >= result >= y[i1]):
                result = np.mean(
                    [r for r in results if y[i0] < r < y[i1] or y[i0] > r > y[i1]]
                )

            if np.isnan(result):
                result = self.linear_expr(x[i0], x[i1], y[i0], y[i1], base)

        return round(result, 2)

    @staticmethod
    def make_expr(a, b):
        """
        Make condition for impl_vol comparison
        :param a: float
        :param b: float
        :return: str, str
        """
        if a > b:
            str0 = '{iv0} > {r} > {iv1}'
            str1 = '{linear} > {r}'
        elif a < b:
            str0 = '{iv0} < {r} < {iv1}'
            str1 = '{linear} < {r}'
        else:
            raise ArithmeticError('a == b, %.2f == %.2f' % (a, b))

        return str0, str1

    @staticmethod
    def estimate_errors(f, dtes, impl_vols):
        """
        Estimate errors for poly1d function
        :param f: np.poly1d
        :param dtes: list
        :param impl_vols: list
        :return: list
        """
        errors = []
        for a, b in zip(dtes, impl_vols):
            errors.append(round(f(a) - b, 2))

        return errors

    @staticmethod
    def single_cond(result, iv0, iv1):
        """
        Check close price is above/below all strikes valid
        :param result: float
        :param iv0: float
        :param iv1: float
        """
        if iv0 < iv1:
            if result > iv0:
                print output % ('COND', 'linear_iv < impl_vol0, %.2f < %.2f, %s' % (
                    result, iv0, result < iv0
                ))
                raise ValueError('invalid result linear_iv < impl_vol0')
        elif iv0 > iv1:
            if result < iv0:
                print output % ('COND', 'linear_iv > impl_vol0, %.2f > %.2f, %s' % (
                    result, iv0, result > iv0
                ))
                raise ValueError('invalid result linear_iv < impl_vol0')

    def reduce_samples(self, base, x, y):
        """
        Reduce sample size for better estimate calculation
        :param base: float
        :param x: list
        :param y: list
        :return: int, int, list, list
        """
        b0, b1 = self.two_nearby(x, base)
        if x[b0] <= base <= x[b1]:
            i0, i1 = self.list_index(x, b0, b1, 1)
        else:
            i0, i1 = self.list_index(x, b0, b1, 0)
        x = x[i0:i1]
        y = y[i0:i1]
        b0, b1 = self.two_nearby(x, base)
        return b0, b1, x, y

    def poly1d_expr(self, close, linear_iv, b0, b1, bases, impl_vols):
        """
        Calc poly1d impl_vol using numpy builtin method
        :param close: float
        :param linear_iv: float
        :param b0: int
        :param b1: int
        :param bases: list
        :param impl_vols: list
        :return: float
        """
        if impl_vols[b0] == impl_vols[b1]:
            return impl_vols[b0]

        str0, _ = self.make_expr(impl_vols[b0], impl_vols[b1])
        cond0 = str0.format(iv0='iv0', r='poly1d_iv', iv1='iv1')
        results = []
        for degree in range(1, 4):
            z = np.polyfit(bases, impl_vols, degree)
            f = np.poly1d(z)
            result = round(f(close), 2)
            print output % ('CALC', 'degree: %d, impl_vol: %.2f' % (degree, result))
            arg0 = str0.format(iv0=impl_vols[b0], r=result, iv1=impl_vols[b1])
            print output % ('COND', '%s, %s, %s' % (cond0, arg0, eval(arg0)))

            if eval(arg0):
                results.append(result)

        poly1d_iv = linear_iv
        if len(results):
            poly1d_iv = np.mean(results)

        return poly1d_iv


# dte method
class DaySingleDte2dCalc(DayImplVolStatic):
    def __init__(self, close, days, df_date):
        """
        :param close: float
        :param days: int
        :param df_date: pd.DataFrame
        """
        self.close = close
        self.days = days
        self.df_date = df_date

    def estimate(self):
        """
        When only 1 dte in df_date, using direct math method calc
        :return: float, float, float
        """
        print output % ('PROC', 'calc iv when only one dte in df_date')
        print '-' * 70

        df_dte = self.df_date.sort_values('strike')
        dte = df_dte['dte'].unique()[0]
        print output % ('SEED', 'close: %.2f, dte: %d, df_date: %d' % (
            self.close, self.days, len(df_dte)
        ))
        strikes = np.array(df_dte['strike'])
        impl_vols = np.array(df_dte['impl_vol'])

        # correct index and reduce sample
        if self.close < strikes.min():
            s0, s1 = 0, 1
            strikes = strikes[s0:s1 + 1]
            impl_vols = impl_vols[s0:s1 + 1]
        elif self.close > strikes.max():
            s0, s1 = len(strikes) - 1, len(strikes) - 2
            strikes = strikes[s1 - 1:s0]
            impl_vols = impl_vols[s1 - 1:s0]
            s0, s1 = 0, 1
        else:
            s0, s1, strikes, impl_vols = self.reduce_samples(self.close, strikes, impl_vols)

        print output % ('DATA', 'strikes: %s' % strikes)

        print output % ('NEAR', 'dte: %d, strike0: %d(%.2f), strike1: %d(%.2f)' % (
            dte, s0, strikes[s0], s1, strikes[s1]
        ))

        if len(strikes) == 1:
            raise KeyError('df_date only have 1 strike in 1 dte, unable to calc')

        # (Annualized Implied Volatility) x (Square Root of [days to expiration / 365])
        results = []
        for strike, impl_vol in zip(strikes, impl_vols):
            print output % ('DATA', 'strike: %.2f, impl_vol: %.2f' % (strike, impl_vol))
            strike_iv = impl_vol * (self.days / dte)
            print output % ('CALC', '1 std $%.2f: %.2f' % (strike, strike_iv))
            print '-' * 70

            results.append((strike, strike_iv))

        strikes = np.array([r[0] for r in results])
        impl_vols = np.array([round(r[1], 2) for r in results])

        if len(strikes) == 2:
            linear_iv = self.linear_expr(
                strikes[s0], strikes[s1], impl_vols[s0], impl_vols[s1], self.close
            )
            range_iv = poly1d_iv = linear_iv
        else:
            linear_iv = self.linear_expr(
                strikes[s0], strikes[s1], impl_vols[s0], impl_vols[s1], self.close
            )
            range_iv = self.range_expr(strikes, impl_vols, self.close)
            poly1d_iv = self.poly1d_expr(self.close, linear_iv, s0, s1, strikes, impl_vols)

        print '-' * 70
        print output % ('CALC', 'linear_iv %d-days: %.2f' % (self.days, linear_iv))
        print output % ('CALC', 'range_iv %d-days: %.2f' % (self.days, range_iv))
        print output % ('CALC', 'poly1d_iv %d-days: %.2f' % (self.days, poly1d_iv))
        print '-' * 70

        return linear_iv, range_iv, poly1d_iv


class DayInDte2dCalc(DayImplVolStatic):
    def __init__(self, close, days, df_date):
        """
        :param close: float
        :param days: int
        :param df_date: pd.DataFrame
        """
        self.close = close
        self.days = days
        self.df_date = df_date

    def exact_close_in_strikes(self, df_dte):
        """
        Exact close price in df_dte strike, get impl_vol
        :param df_dte: pd.DataFrame
        :return: float, float, float
        """
        impl_vol = df_dte[df_dte['strike'] == self.close].iloc[0]['impl_vol']
        print '-' * 70
        print output % ('CALC', 'direct iv from row: %.2f' % impl_vol)
        print '-' * 70

        return impl_vol, impl_vol, impl_vol

    def close_above_below_strikes(self, pos, df_dte):
        """
        Calc iv when close is above/below strikes
        :param pos: ('above', 'below')
        :param df_dte: pd.DataFrame
        :return: float, float, float
        """
        # get data
        df_dte = df_dte.sort_values('strike')
        strikes = np.array(df_dte['strike'])
        impl_vols = np.array(df_dte['impl_vol'])
        print '-' * 70

        # select index then calculate
        s0, s1 = (len(df_dte) - 1, len(df_dte) - 2) if pos == 'above' else (0, 1)
        print output % ('NEAR', 'strike0: %d(%.2f), strike1: %d(%.2f)' % (
            s0, strikes[s0], s1, strikes[s1]
        ))
        print output % ('NEAR', 'impl_vol0: %d(%.2f), impl_vol1: %d(%.2f)' % (
            s0, impl_vols[s0], s1, impl_vols[s1]
        ))
        linear_iv = self.linear_expr(
            strikes[s0], strikes[s1], impl_vols[s0], impl_vols[s1], self.close
        )
        print output % ('CALC', 'linear_iv == range_iv == poly1d_iv: %.2f' % linear_iv)
        print '-' * 70

        # result condition error checking
        self.single_cond(linear_iv, impl_vols[s0], impl_vols[s1])

        return linear_iv, linear_iv, linear_iv

    def close_within_two_strikes(self, df_dte):
        """
        Calc impl_vol when close is within 2 rows (df_dte only got 2 records)
        :param df_dte: pd.DataFrame
        :return: float, float, float
        """
        strikes = np.array(df_dte['strike'])
        impl_vols = np.array(df_dte['impl_vol'])
        linear_iv = self.linear_expr(
            strikes[0], strikes[1], impl_vols[0], impl_vols[1], self.close
        )
        print '-' * 70
        print output % ('CALC', 'linear_iv: %.2f' % linear_iv)
        print '-' * 70

        return linear_iv, linear_iv, linear_iv

    def close_within_strike_range(self, df_dte):
        """
        Calc impl_vol when more than 2 rows
        :param df_dte:
        :return: float, float, float
        """
        print '-' * 70
        print output % ('DATA', 'close: %.2f, df_dte: %d' % (self.close, len(df_dte)))
        strikes = np.array(df_dte['strike'])
        impl_vols = np.array(df_dte['impl_vol'])
        close = self.close
        s0, s1, strikes, impl_vols = self.reduce_samples(close, strikes, impl_vols)
        print output % ('NEAR', 'strike0: %d(%.2f), strike1: %d(%.2f)' % (
            s0, strikes[s0], s1, strikes[s1]
        ))
        print '-' * 70

        for a, b in zip(strikes, impl_vols):
            print output % ('DATA', 'strike: %.2f, impl_vol: %.2f' % (a, b))

        print '-' * 70
        linear_iv = self.linear_expr(strikes[s0], strikes[s1], impl_vols[s0], impl_vols[s1], close)
        range_iv = self.range_expr(strikes, impl_vols, close)
        print '-' * 70
        poly1d_iv = self.poly1d_expr(close, linear_iv, s0, s1, strikes, impl_vols)
        print '-' * 70
        print output % ('CALC', 'linear_iv %.2f: %.2f' % (close, linear_iv))
        print output % ('CALC', 'range_iv %.2f: %.2f' % (close, range_iv))
        print output % ('CALC', 'poly1d_iv %.2f: %.2f' % (close, poly1d_iv))
        print '-' * 70

        return linear_iv, range_iv, poly1d_iv

    def estimate(self):
        """
        two different type of calculate method
        1. close price within up and down range strike
        2. close price is below/above all strike
        :return:
        """
        print '-' * 70
        print output % ('PROC', '365-days exists in dte cycle, direct process')
        # print self.df_date.to_string(line_width=1000)
        close = round(self.close, 2)
        df_dte = self.df_date.query('dte == %d' % self.days).sort_values('strike')
        linear_iv, range_iv, poly_iv = 0, 0, 0
        print output % ('SEED', 'close: %.2f, df_dte: %d' % (close, len(df_dte)))

        if len(df_dte) < 2:  # less than 2 rows in df_dte, error
            print output % ('ERROR', 'df_dte less than 2 rows: %d' % len(df_dte))
            raise LookupError('No enough data in df_dte length: %d' % len(df_dte))
        else:  # 2 rows or more in df_dte
            strikes = [round(s, 2) for s in df_dte['strike']]

            if close in strikes:  # close found in strike direct use impl_vol
                linear_iv, range_iv, poly_iv = self.exact_close_in_strikes(df_dte)
            elif close < strikes[0]:
                # lower single nearby strike in exact dte, use linear
                linear_iv, range_iv, poly_iv = self.close_above_below_strikes('below', df_dte)
            elif strikes[-1] < close:
                # higher single nearby strike in exact dte, use linear
                linear_iv, range_iv, poly_iv = self.close_above_below_strikes('above', df_dte)
            else:
                # close in range with more than 2 row in df_dte
                if len(df_dte) == 2:  # exactly 2, use linear
                    linear_iv = self.close_within_two_strikes(df_dte)
                else:  # more than 2, use linear, range, poly
                    linear_iv, range_iv, poly_iv = self.close_within_strike_range(df_dte)

        print '=' * 70

        return linear_iv, range_iv, poly_iv


class DayGtLtDtes3dCalc(DayImplVolStatic):
    def __init__(self, close, days, df_date):
        """
        :param close: float
        :param days: int
        :param df_date: pd.DataFrame
        """
        self.close = close
        self.days = days
        self.df_date = df_date

    def estimate(self):
        """
        Days is above/below all dtes and must greater then 2 dte
        must have 2 nearby dtes to calc days iv

        2 nearby dtes,
        both of in range strikes
        one of the in range strikes, one of the in above/below all strikes
        both dtes have above/below all strikes
        :return:
        """
        print output % ('PROC', 'calc iv when days gt/lt dtes')
        print '-' * 70
        df_date = self.df_date.sort_values('dte')
        dtes = np.array(df_date['dte'].unique())
        d0, d1 = self.two_nearby(dtes, self.days)
        print output % ('SEED', 'close: %.2f, days: %d, df_date: %d' % (
            self.close, self.days, len(df_date)
        ))
        print output % ('NEAR', 'dte0: %d(%d), dte1: %d(%d)' % (d0, dtes[d0], d1, dtes[d1]))
        print '-' * 70

        if len(dtes) < 2:
            raise KeyError('Unable calculate when df_dte less than 2 rows')

        dtes = [dtes[d0], dtes[d1]]
        df_date = df_date[df_date['dte'].isin(dtes)]

        results = []
        for dte in dtes:
            df_dte = df_date.query('dte == %r' % dte).sort_values('strike')

            strikes = np.array(df_dte['strike'])
            impl_vols = np.array(df_dte['impl_vol'])
            s0, s1, strikes, impl_vols = self.reduce_samples(self.close, strikes, impl_vols)

            print output % ('NEAR', 'strike0: %d(%.2f), strike1: %d(%.2f)' % (
                s0, strikes[s0], s1, strikes[s1]
            ))

            print '-' * 70
            for a, b in zip(strikes, impl_vols):
                print output % ('DATA', 'strike: %.2f, impl_vol: %.2f' % (a, b))
            print '-' * 70

            dte_linear_iv = self.linear_expr(
                strikes[s0], strikes[s1], impl_vols[s0], impl_vols[s1], self.close
            )
            dte_range_iv = dte_poly1d_iv = dte_linear_iv
            print output % ('CALC', 'linear_iv $%.2f: %.2f' % (self.close, dte_linear_iv))

            if len(strikes) > 2:
                dte_range_iv = self.range_expr(strikes, impl_vols, self.close)
                dte_poly1d_iv = self.poly1d_expr(self.close, dte_linear_iv, s0, s1, strikes, impl_vols)
                print output % ('CALC', 'range_iv $%.2f: %.2f' % (self.close, dte_range_iv))
                print output % ('CALC', 'poly1d_iv $%.2f: %.2f' % (self.close, dte_poly1d_iv))

            results.append((dte, dte_linear_iv, dte_range_iv, dte_poly1d_iv))
            print '-' * 70

        # calc iv
        dtes = [r[0] for r in results]
        linear_ivs = [r[1] for r in results]
        range_ivs = [r[2] for r in results]
        poly1d_ivs = [r[3] for r in results]

        if len(dtes) == 2:
            linear_iv = self.linear_expr(dtes[0], dtes[1], linear_ivs[0], linear_ivs[1], self.days)
            range_iv = self.linear_expr(dtes[0], dtes[1], range_ivs[0], range_ivs[1], self.days)
            poly1d_iv = self.linear_expr(dtes[0], dtes[1], poly1d_ivs[0], poly1d_ivs[1], self.days)
        else:
            linear_iv = self.range_expr(dtes, linear_ivs, self.days)
            range_iv = self.range_expr(dtes, range_ivs, self.days)
            poly1d_iv = self.range_expr(dtes, poly1d_ivs, self.days)

        print output % ('CALC', 'linear_iv %d-days: %.2f' % (self.days, linear_iv))
        print output % ('CALC', 'range_iv %d-days: %.2f' % (self.days, range_iv))
        print output % ('CALC', 'poly1d_iv %d-days: %.2f' % (self.days, poly1d_iv))
        print '-' * 70

        return linear_iv, range_iv, poly1d_iv


class DayInRangeDtes3dCalc(DayImplVolStatic):
    def __init__(self, close, days, df_date):
        """
        :param close: float
        :param days: int
        :param df_date: pd.DataFrame
        """
        self.close = close
        self.days = days
        self.df_date = df_date

    def estimate(self):
        """
        Calc iv when days in range dtes
        """
        print output % ('PROC', 'calc iv when days gt/lt dtes')
        print '-' * 70
        df_date = self.df_date.sort_values('dte')
        dtes = np.array(df_date['dte'].unique())
        d0, d1 = self.two_nearby(dtes, self.days)

        print output % ('SEED', 'close: %.2f, days: %d, df_date: %d' % (
            self.close, self.days, len(df_date)
        ))
        print output % ('NEAR', 'dte0: %d(%d), dte1: %d(%d)' % (d0, dtes[d0], d1, dtes[d1]))
        i0, i1 = self.list_index(dtes, d0, d1, 1)
        df_date = df_date[df_date['dte'].isin(dtes[i0:i1])]
        dtes = np.sort(df_date['dte'].unique())
        print output % ('DATA', 'dtes: %s' % dtes)
        print '-' * 70

        if len(dtes) < 2:
            raise KeyError('Unable calculate when df_dte less than 2 rows')

        results = []
        for dte in dtes:
            df_dte = df_date.query('dte == %r' % dte).sort_values('strike')
            print output % ('LOOP', 'running dte: %d' % len(df_dte))

            strikes = np.array(df_dte['strike'])
            impl_vols = np.array(df_dte['impl_vol'])
            # auto reduce to nearby (if strike is above/below also correct)
            s0, s1, strikes, impl_vols = self.reduce_samples(self.close, strikes, impl_vols)

            print output % ('NEAR', 'strike0: %d(%.2f), strike1: %d(%.2f)' % (
                s0, strikes[s0], s1, strikes[s1]
            ))

            print '-' * 70
            for a, b in zip(strikes, impl_vols):
                print output % ('DATA', 'strike: %.2f, impl_vol: %.2f' % (a, b))
            print '-' * 70

            linear_iv = self.linear_expr(
                strikes[s0], strikes[s1], impl_vols[s0], impl_vols[s1], self.close
            )
            range_iv = poly1d_iv = linear_iv
            print output % ('CALC', 'linear_iv %d-days: %.2f' % (dte, linear_iv))

            if len(strikes) > 2:  # if more than 2 strikes, then do range, poly1d
                range_iv = self.range_expr(strikes, impl_vols, self.close)
                poly1d_iv = self.poly1d_expr(self.close, linear_iv, s0, s1, strikes, impl_vols)
                print output % ('CALC', 'range_iv %d-days: %.2f' % (dte, range_iv))
                print output % ('CALC', 'poly1d_iv %d-days: %.2f' % (dte, poly1d_iv))

            results.append((dte, linear_iv, range_iv, poly1d_iv))
            print '-' * 70

        # calc iv
        dtes = [r[0] for r in results]
        linear_ivs = [r[1] for r in results]
        range_ivs = [r[2] for r in results]
        poly1d_ivs = [r[3] for r in results]

        if len(dtes) == 2:
            linear_iv = self.linear_expr(dtes[0], dtes[1], linear_ivs[0], linear_ivs[1], self.days)
            range_iv = self.linear_expr(dtes[0], dtes[1], range_ivs[0], range_ivs[1], self.days)
            poly1d_iv = self.linear_expr(dtes[0], dtes[1], poly1d_ivs[0], poly1d_ivs[1], self.days)
        else:
            linear_iv = self.range_expr(dtes, linear_ivs, self.days)
            range_iv = self.range_expr(dtes, range_ivs, self.days)
            poly1d_iv = self.range_expr(dtes, poly1d_ivs, self.days)

        print output % ('CALC', 'linear_iv %d-days: %.2f' % (self.days, linear_iv))
        print output % ('CALC', 'range_iv %d-days: %.2f' % (self.days, range_iv))
        print output % ('CALC', 'poly1d_iv %d-days: %.2f' % (self.days, poly1d_iv))
        print '-' * 70

        return linear_iv, range_iv, poly1d_iv


# strike method
class ExactStrike2dCalc(DayImplVolStatic):
    def __init__(self, close, days, df_date):
        """
        :param close: float
        :param days: int
        :param df_date: pd.DataFrame
        """
        self.close = close
        self.days = days
        self.df_date = df_date

    def days_within_two_dtes(self, df_strike):
        """
        Calc impl_vol when df_dte only have 2 rows
        :param df_strike: pd.DataFrame
        :return: float, float, float
        """
        print '-' * 70
        print output % ('PROC', 'calc exact close strike with df_dte == 2')
        df_strike = df_strike.sort_values('dte')
        dtes = np.array(df_strike['dte'])
        impl_vols = np.array(df_strike['impl_vol'])
        d0, d1 = (0, 1)
        print output % ('NEAR', 'dte0: %d(%d) dte1: %d(%d)' % (d0, dtes[d0], d1, dtes[d1]))
        print '-' * 70
        for a, b in zip(dtes, impl_vols):
            print output % ('DATA', 'dte: %d, impl_vol: %.2f' % (a, b))
        print '-' * 70
        linear_iv = self.linear_expr(dtes[d0], dtes[d1], impl_vols[d0], impl_vols[d1], self.days)
        print output % ('CALC', 'linear_iv: %.2f' % linear_iv)
        print '-' * 70

        return linear_iv, linear_iv, linear_iv

    def days_within_range_dtes(self, df_strike):
        """
        Calc impl_vol when df_dte have more than 2 rows
        :param df_strike: pd.DataFrame
        :return: float, float, float
        """
        print '-' * 70
        print output % ('PROC', 'calc exact close strike with df_dte > 2')
        df_strike = df_strike.sort_values('dte')
        dtes = np.array(df_strike['dte'])
        impl_vols = np.array(df_strike['impl_vol'])
        d0, d1, dtes, impl_vols = self.reduce_samples(self.days, dtes, impl_vols)
        print output % ('NEAR', 'dte0: %d(%d) dte1: %d(%d)' % (d0, dtes[d0], d1, dtes[d1]))
        print '-' * 70
        for a, b in zip(dtes, impl_vols):
            print output % ('DATA', 'dte: %d, impl_vol: %.2f' % (a, b))
        print '-' * 70

        linear_iv = self.linear_expr(dtes[d0], dtes[d1], impl_vols[d0], impl_vols[d1], self.days)
        range_iv = self.range_expr(dtes, impl_vols, self.days)
        poly1d_iv = self.poly1d_expr(self.close, linear_iv, d0, d1, dtes, impl_vols)
        print output % ('CALC', 'linear_iv: %.2f' % linear_iv)
        print output % ('CALC', 'range_iv: %.2f' % range_iv)
        print output % ('CALC', 'poly1d_iv: %.2f' % poly1d_iv)
        print '-' * 70

        return linear_iv, range_iv, poly1d_iv

    def estimate(self):
        """
        Use this when no exact dte, day in dte0, dte1, close strike in both dtes
        Calc iv when found exact close price strike in range cycle
        :return: float, float, float
        """
        df_strike = self.df_date.query('strike == %.2f' % self.close)

        if len(df_strike) == 2:  # exact 2 rows, use linear
            linear_iv, range_iv, poly1d_iv = self.days_within_two_dtes(df_strike)
        else:  # more than 2 rows, calc all
            linear_iv, range_iv, poly1d_iv = self.days_within_range_dtes(df_strike)

        print '=' * 70

        return linear_iv, range_iv, poly1d_iv


class CloseGtLtStrikes3dCalc(DayImplVolStatic):
    def __init__(self, close, days, df_date):
        """
        :param close: float
        :param days: int
        :param df_date: pd.DataFrame
        """
        self.close = close
        self.days = days
        self.df_date = df_date

    def strikes_in_range_dtes(self, df_dte):
        """

        :param pos: str ('above', 'below')
        :param df_dte: pd.DataFrame
        :return: float, float, float
        """
        #print df_dte.to_string(line_width=1000)
        count = df_dte['strike'].value_counts()
        strikes = count[count == 2].index




        pass

    def strikes_in_range_with_gt_2dtes(self, df_date):
        """

        :param df_date:
        :return:
        """
        print '-' * 70
        print output % ('PROC', 'close is above/below strikes within range dtes')
        print '-' * 70

        print df_date.to_string(line_width=1000)
        df_date = df_date.sort_values(['dte', 'strike'])
        dtes = np.array(df_date['dte'].unique())
        d0, d1 = self.two_nearby(dtes, self.days)
        print output % ('NEAR', 'dte0: %d(%d), dte1: %d(%d)' % (
            d0, dtes[d0], d1, dtes[d1]
        ))

        group = df_date.groupby('dte')
        print group['strike'].min()

        # todo: rework using multi loop each dte decide what to use

    def estimate(self):
        """
        Close is above/below all strikes in both range dtes
        must be in range dtes and each dte need 2 rows
        :return: float, float, float
        """
        print '-' * 70
        print output % ('PROC', 'close is above/below strikes within range dtes')
        print '-' * 70

        df_date = self.df_date.sort_values(['dte', 'strike'])
        dtes = np.array(df_date['dte'].unique())
        d0, d1 = self.two_nearby(dtes, self.days)
        print output % ('NEAR', 'dte0: %d(%d), dte1: %d(%d)' % (
            d0, dtes[d0], d1, dtes[d1]
        ))
        dtes = np.array([dtes[d0], dtes[d1]])
        df_dte = df_date[df_date['dte'].isin(dtes)]
        d0, d1 = 0, 1
        count = df_dte['strike'].value_counts()
        strikes = np.sort(count[count == 2].index)
        df_dte = df_dte[df_dte['strike'].isin(strikes)]

        if self.close < strikes.min():
            s0, s1 = 0, 1
            print 'min', s0, s1
        elif self.close > strikes.max():
            s0, s1 = len(strikes) - 1, len(strikes) - 2
            print 'max', s0, s1
        else:
            raise ValueError('Exact close strike found')

        print output % ('NEAR', 'strike0: %d(%.2f), strike1: %d(%.2f)' % (
            s0, strikes[s0], s1, strikes[s1]
        ))

        dte_ivs = []
        for dte in dtes:
            df = df_dte[df_dte['dte'] == dte]
            print output % ('DATA', 'dte: %d, df_dte: %d' % (dte, len(df)))

            strikes = np.array(df['strike'])
            impl_vols = np.array(df['impl_vol'])
            print '-' * 70
            for a, b in zip(strikes, impl_vols)[s0:s1 + 1]:
                print output % ('DATA', 'strike: %.2f, impl_vol: %.2f' % (a, b))
            print '-' * 70

            dte_iv = self.linear_expr(
                strikes[s0], strikes[s1], impl_vols[s0], impl_vols[s1], self.close
            )
            dte_ivs.append(dte_iv)
            print output % ('CALC', 'linear_iv %d-days: %.2f' % (dte, dte_iv))
            print '-' * 70

        for a, b in zip(dtes, dte_ivs):
            print output % ('DATA', 'dte: %d, impl_vol: %.2f' % (a, b))
        print '-' * 70

        linear_iv = self.linear_expr(dtes[d0], dtes[d1], dte_ivs[d0], dte_ivs[d1], self.days)
        print output % ('CALC', 'linear_iv %d-days: %.2f' % (self.days, linear_iv))
        print '=' * 70

        return linear_iv, linear_iv, linear_iv





class MultiStrikeToStrike3dCalc(DayImplVolStatic):
    def __init__(self):
        pass


























