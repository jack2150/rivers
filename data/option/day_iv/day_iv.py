import os

import numpy as np
import pandas as pd

from data.models import Underlying
from rivers.settings import QUOTE_DIR, CLEAN_DIR

output = '%-6s | %-s'
calc_days = [30, 60, 90, 150, 365]


class DayImplVolStatic(object):
    # noinspection PyUnresolvedReferences
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
        if index0 > index1:
            temp = index1
            index1 = index0
            index0 = temp

        i0 = index0 - value if index0 - value > -1 else 0
        i1 = index1 + value + 1 if index1 + value + 1 < len(data) else len(data)

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

    def range_expr(self, x, y, base, info=True):
        """
        Triple linear range estimate using median
        :param x: list
        :param y: list
        :param base: float/int
        :param info: bool
        :return: float
        """
        if not len(x) == len(y) >= 3:
            if len(x) == len(y) == 1:
                return y[0]
            elif len(x) == len(y) == 2:
                return self.linear_expr(x[0], x[1], y[0], y[1], base)
            else:
                print x
                print y
                raise ValueError('Range expr x, y list is empty')

        if info:
            for a, b in zip(x, y):
                print output % ('DATA', 'calc range, dte/strike: %.2f, impl_vol: %.2f' % (a, b))

        if len(x) == len(y) == 3:
            d0, d1 = self.two_nearby(x, base)
            if d0 == 1 and d1 == 2:
                iv0 = y[1] + (y[1] - y[0]) / (x[1] - x[0]) * (base - x[1])
                iv1 = self.linear_expr(x[1], x[2], y[1], y[2], base)
                ivs = [iv0, iv1]
                i0, i1 = 1, 2
            else:
                iv1 = self.linear_expr(x[0], x[1], y[0], y[1], base)
                iv2 = y[1] - (y[2] - y[1]) / (x[2] - x[1]) * (x[1] - base)
                ivs = [iv1, iv2]
                i0, i1 = 0, 1
        else:
            iv0 = y[1] + (y[1] - y[0]) / (x[1] - x[0]) * (base - x[1])
            iv1 = self.linear_expr(x[1], x[2], y[1], y[2], base)
            iv2 = y[2] - (y[3] - y[2]) / (x[3] - x[2]) * (x[2] - base)
            ivs = [iv0, iv1, iv2]
            i0, i1 = 1, 2

        if len(ivs) == 1:
            result = ivs[0]
        else:
            result = np.mean(ivs)
            if not (y[i0] <= result <= y[i1] or y[i0] >= result >= y[i1]):
                ivs = [r for r in ivs if y[i0] < r < y[i1] or y[i0] > r > y[i1]]
                if len(ivs):
                    result = np.mean(ivs)
                else:
                    result = self.linear_expr(x[i0], x[i1], y[i0], y[i1], base)

            if np.isnan(result):
                result = self.linear_expr(x[i0], x[i1], y[i0], y[i1], base)

        if info:
            print output % ('NEAR', 'index0: %d, index1: %d' % (i0, i1))
            print output % ('CALC', 'range_ivs: %s' % [round(r, 2) for r in ivs])

        return round(result, 2)

    # todo: gg, empty list???

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


class DayIVCalc(object):
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
        db = pd.HDFStore(os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower()))
        self.df_stock = db.select('stock/thinkback')
        # df_contract = db.select('option/%s/final/contract' % self.symbol.lower())
        # df_option = db.select('option/%s/final/data' % self.symbol.lower())
        # self.df_all = pd.merge(df_option, df_contract, on='option_code')
        db.close()

        path = os.path.join(CLEAN_DIR, '__%s__.h5' % self.symbol.lower())
        db = pd.HDFStore(path)
        df_normal = db.select('iv/clean/normal')
        path = '/iv/clean/split/old'
        df_split0 = pd.DataFrame()
        if path in db.keys():
            df_split0 = db.select(path)
        db.close()

        if len(df_split0):
            self.df_all = pd.concat([df_normal, df_split0])
            """:type: pd.DataFrame"""
        else:
            self.df_all = df_normal.copy()
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
        df_date = df_date[['date', 'dte', 'strike', 'impl_vol']]

        return df_date.copy()

    def calc_iv(self):
        """
        Get everyday data then using 3d fill all strike method
        then calc iv using dte and strike method
        :return: pd.DataFrame
        """
        result_ivs = []
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

            # check strikes
            strikes = np.sort(df_date['strike'].unique())
            s0, s1 = self.static.two_nearby(strikes, close)

            if close in strikes:  # if close is exists in strikes
                i0, i1 = self.static.list_index(strikes, s0, s1, 1)
                strikes = strikes[i0:i1]
            elif strikes[s0] <= close <= strikes[s1]:  # if not in range
                i0, i1 = self.static.list_index(strikes, s0, s1, 1)
                strikes = strikes[i0:i1]
            else:  # if in range
                i0, i1 = self.static.list_index(strikes, s0, s1, 0)
                strikes = strikes[i0:i1]

            if close not in list(strikes):
                strikes = np.append(strikes, close)  # need to be last

            dtes = np.sort(df_date['dte'].unique())
            print output % ('DATA', 'exists dtes: %s' % dtes)
            print output % ('DATA', 'require strike: %s' % strikes)

            dte_filled = []
            for dte in dtes:
                df_dte = df_date[df_date['dte'] == dte]
                dte_strikes = np.sort(df_dte['strike'])

                print output % ('LOOP', 'dte: %d, df_dte: %d' % (dte, len(df_dte)))
                for strike in strikes:
                    if strike not in dte_strikes:
                        calc = StrikeNotInDtes2dCalc(strike, dte, df_dte)
                        dte_iv = calc.approx()

                        if dte_iv > 0:
                            dte_filled.append({
                                'date': date,
                                'dte': dte,
                                'strike': strike,
                                'impl_vol': dte_iv
                            })
                        else:
                            continue

                print '-' * 70

            df_fill0 = pd.DataFrame(dte_filled)
            df_fill0 = pd.concat([df_date, df_fill0])
            """:type: pd.DataFrame"""
            df_fill0 = df_fill0[df_fill0['strike'].isin(strikes)].sort_values(['dte', 'strike'])

            print '=' * 70

            # check dte
            dtes = list(dtes)
            days = [d for d in calc_days if d not in dtes]
            strikes = [s for s in strikes if s != close]

            day_filled = []
            for day in days:
                print output % ('LOOP', 'day: %d' % day)

                d0, d1 = self.static.two_nearby(dtes, day)
                if dtes[d0] <= close <= dtes[d1]:  # if not in range
                    i0, i1 = self.static.list_index(dtes, d0, d1, 1)
                    nearby_dtes = dtes[i0:i1]
                else:  # if in range
                    i0, i1 = self.static.list_index(dtes, d0, d1, 0)
                    nearby_dtes = dtes[i0:i1]

                print output % ('NEAR', 'dte0: %d(%d) dte1: %d(%d)' % (
                    d0, dtes[d0], d1, dtes[d1]
                ))
                print output % ('DATA', 'dtes: %s' % list(nearby_dtes))

                for strike in strikes:
                    df_strike = df_fill0[df_fill0['strike'] == strike].sort_values('dte')
                    calc = DayNotInStrikes2dCalc(day, strike, df_strike)
                    strike_iv = calc.approx()

                    day_filled.append({
                        'date': date,
                        'dte': day,
                        'strike': strike,
                        'dte_iv': strike_iv,
                        'strike_iv': strike_iv,
                        'impl_vol': strike_iv
                    })

            # calc both strike/dte iv
            df_fill1 = pd.DataFrame(day_filled)
            df_fill = pd.concat([df_fill0, df_fill1])
            """:type: pd.DataFrame"""

            days_iv = []
            for day in calc_days:
                df_dte = df_fill[df_fill['dte'] == day]
                # noinspection PyTypeChecker
                if not np.any(df_dte['strike'] == close):
                    # 3d calc iv only require when no dte strike exists
                    calc = StrikeNotInDtes2dCalc(close, day, df_dte)
                    dte_iv = calc.approx()

                    print '-' * 70

                    df_strike = df_fill[df_fill['strike'] == close]
                    calc = DayNotInStrikes2dCalc(day, close, df_strike)
                    strike_iv = calc.approx()
                    impl_vol = np.mean([iv for iv in (dte_iv, strike_iv) if iv > 0])

                    days_iv.append({
                        'date': date,
                        'dte': day,
                        'strike': close,
                        'dte_iv': dte_iv,
                        'strike_iv': strike_iv,
                        'impl_vol': impl_vol
                    })

            # result iv
            df_iv0 = df_fill0[(df_fill0['dte'].isin(calc_days)) & (df_fill0['strike'] == close)]
            df_iv1 = pd.DataFrame(
                days_iv, columns=['date', 'dte', 'strike', 'dte_iv', 'strike_iv', 'impl_vol']
            )

            if len(df_iv0):
                df_days = pd.concat([df_iv0, df_iv1])
                """:type: pd.DataFrame"""
            else:
                df_days = df_iv1

            assert len(df_days) == len(calc_days)

            result_ivs.append(df_days)

        print output % ('LAST', 'final merge df_iv: %d' % len(result_ivs))
        df_iv = pd.concat(result_ivs)
        """:type: pd.DataFrame"""

        # format dataframe
        df_iv['symbol'] = str(self.symbol.upper())
        df_iv = df_iv[[
            'date', 'dte', 'dte_iv', 'strike_iv', 'impl_vol'
        ]]
        df_iv['dte'] = df_iv['dte'].astype('int')
        df_iv = df_iv.round({'dte_iv': 2, 'strike_iv': 2, 'impl_vol': 2})
        df_iv = df_iv.reset_index(drop=True)

        return df_iv

    def save_iv(self, df_iv):
        """
        Save df_iv into quote db
        :param df_iv: pd.DataFrame
        """
        print output % ('DB', 'open quote db')
        path = '/option/iv/day'
        db = pd.HDFStore(os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower()))
        try:
            print output % ('DB', 'old table remove: %s' % path)
            db.remove(path)
        except KeyError:
            pass
        print output % ('DB', 'append new table')
        db.append(path, df_iv, format='table', data_columns=True, min_itemsize=100)
        db.close()
        print output % ('DB', 'close quote db')

    def start(self):
        """
        Start calc days iv using options
        """
        self.get_data()
        print '+' * 70
        df_iv = self.calc_iv()
        print '+' * 70
        self.save_iv(df_iv)

        Underlying.write_log(self.symbol, ['DayIV calc, df_iv: %d' % len(df_iv)])


class StrikeNotInDtes2dCalc(DayImplVolStatic):
    def __init__(self, strike, dte, df_dte):
        """
        :param strike: float
        :param dte: int
        :param df_dte: pd.DataFrame
        """
        self.strike = strike
        self.dte = dte
        self.df_dte = df_dte

    def approx(self):
        """
        Calc dte strike impl_vol that not exists in df_dte
        :return: float
        """
        print output % ('PROC', 'calc strike $%.2f for %d-dte with df_strike' % (
            self.strike, self.dte
        ))
        print '-' * 70
        df_dte = self.df_dte.sort_values('strike')
        if len(df_dte) < 2:
            raise LookupError('Invalid df_dte length: %d' % len(df_dte))

        # reduce strike sample
        strikes = np.array(df_dte['strike'])
        s0, s1 = self.two_nearby(strikes, self.strike)
        if strikes[s0] <= self.strike <= strikes[s1]:  # if in range
            i0, i1 = self.list_index(strikes, s0, s1, 1)
            strikes = strikes[i0:i1]
            s0, s1 = self.two_nearby(strikes, self.strike)
        else:  # if not in range
            i0, i1 = self.list_index(strikes, s0, s1, 0)
            strikes = strikes[i0:i1]
            s0, s1 = self.two_nearby(strikes, self.strike)

        # get strike, impl_vols data
        df_dte = df_dte[df_dte['strike'].isin(strikes)].sort_values('strike')
        impl_vols = np.array(df_dte['impl_vol'])
        print output % ('NEAR', 'strike0: %d(%.2f), strike1: %d(%.2f)' % (
            s0, strikes[s0], s1, strikes[s1]
        ))
        print '-' * 70
        for a, b in zip(strikes, impl_vols):
            print output % ('DATA', 'strike: %.2f, impl_vol: %.2f' % (a, b))
        print '-' * 70

        # calc dte_iv
        if len(strikes) == 2:
            dte_iv = self.linear_expr(
                strikes[s0], strikes[s1], impl_vols[s0], impl_vols[s1], self.strike
            )
        elif len(strikes) > 2:
            dte_iv = self.range_expr(strikes, impl_vols, self.strike)
        else:
            dte_iv = 0

        print output % ('CALC', 'dte_iv for $%.2f: %.2f' % (self.strike, dte_iv))

        return dte_iv


class DayNotInStrikes2dCalc(DayImplVolStatic):
    def __init__(self, days, strike, df_strike):
        """
        :param days: int
        :param strike: float
        :param df_strike: pd.DataFrame
        """
        self.days = days
        self.strike = strike
        self.df_strike = df_strike

    def approx(self):
        """
        Calc dte strike impl_vol that not exists in df_dte
        :return: float
        """
        print output % ('PROC', 'calc %d-dte strike $%.2f with df_strike' % (
            self.days, self.strike
        ))
        print '-' * 70
        df_strike = self.df_strike.sort_values('dte')
        if len(df_strike) < 2:
            raise LookupError('Invalid df_strike length: %d' % len(df_strike))

        # reduce strike sample
        dtes = np.array(df_strike['dte'])
        d0, d1 = self.two_nearby(dtes, self.days)
        if dtes[d0] <= self.days <= dtes[d1]:  # if in range
            i0, i1 = self.list_index(dtes, d0, d1, 1)
            dtes = dtes[i0:i1]
            d0, d1 = self.two_nearby(dtes, self.days)
        else:  # if not in range
            i0, i1 = self.list_index(dtes, d0, d1, 0)
            dtes = dtes[i0:i1]
            d0, d1 = self.two_nearby(dtes, self.days)

        # get strike, impl_vols data
        df_strike = df_strike[df_strike['dte'].isin(dtes)].sort_values('dte')
        impl_vols = np.array(df_strike['impl_vol'])
        print output % ('NEAR', 'dte0: %d(%d), dte1: %d(%d)' % (d0, dtes[d0], d1, dtes[d1]))
        print '-' * 70
        for a, b in zip(dtes, impl_vols):
            print output % ('DATA', 'dte: %.2f, impl_vol: %.2f' % (a, b))
        print '-' * 70

        # calc strike_iv
        if len(dtes) == 2:
            strike_iv = self.linear_expr(
                dtes[d0], dtes[d1], impl_vols[d0], impl_vols[d1], self.days
            )
        else:

            strike_iv = self.range_expr(dtes, impl_vols, self.days)

        print output % ('CALC', 'strike_iv for %d-days: %.2f' % (self.days, strike_iv))

        return strike_iv
