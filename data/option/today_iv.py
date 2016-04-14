import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pprint import pprint
from pandas.tseries.offsets import BDay, Day

from rivers.settings import QUOTE, CLEAN

output = '%-6s | %-s'


class TodayIV(object):
    def __init__(self, symbol):
        self.symbol = symbol.lower()
        self.df_stock = pd.DataFrame()
        self.df_all = pd.DataFrame()

    def get_data(self):
        """
        Get data from hdf5 db
        """
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
        return round(y0 + ((y1 - y0) / (x1 - x0) * (base - x0)), 2)

    def range_expr(self, x, y, base):
        """
        Triple linear range estimate using median
        :param x: list
        :param y: list
        :param base: float/int
        :return: float
        """
        if not len(x) == len(y) >= 3:
            raise ValueError('Input list should have greater than 3')

        for a, b in zip(x, y):
            print output % ('DATA', 'calc range, strike: %.2f, impl_vol: %.2f' % (a, b))

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

        result = np.mean(results)
        if not (y[i0] <= result <= y[i1] or y[i0] >= result >= y[i1]):
            result = np.mean([
                r for r in results if y[i0] < r < y[i1] or y[i0] > r > y[i1]
            ])

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
    def format_data(df_date):
        """

        :param df_date:
        :return:
        """
        # remove 0 impl_vol and 0 days
        df_date = df_date.query('impl_vol > 0').copy()

        # remove split
        rights = df_date['right'].unique()
        if len(rights) > 1:
            print output % ('SPLIT', 'rights: %s' % list(rights))
            df_split = df_date.query('right != "100"')
            df_normal = df_date.query('right == "100"')
            if len(df_normal) and len(df_split):
                length0 = len(df_date)

                print output % ('SPLIT', 'remove duplicate split/normal rows')
                dup_dtes = df_split['dte'].isin(df_normal['dte'].unique())
                dup_strike = ~df_split['strike'].isin(df_normal['strike'].unique())

                df_date = pd.concat([
                    df_normal,
                    df_split[dup_dtes & dup_strike]
                ])
                """:type: pd.DataFrame"""

                length1 = len(df_date)
                print output % ('DATA', 'df_date0: %d, df_date1: %d' % (length0, length1))

        return df_date.copy()

    def nearby_365days(self, close, dte, df_date):
        """
        If 365-days in dte, use direct estimate,
        get the 365-days cycles, calculate the close price strike
        :param close: float
        :param dte: int
        :param df_date: pd.datetime
        :return: float, float
        """
        print output % ('PROC', '365-days exists in dte cycle, direct process')
        df_dte = df_date.query('dte == %r' % dte).sort_values('strike')
        print output % ('SEED', 'close: %.2f, df_dte: %d' % (close, len(df_dte)))

        # find nearest
        strikes = np.array(df_dte['strike'])
        impl_vols = np.array(df_dte['impl_vol'])
        s0, s1 = self.two_nearby(strikes, close)
        i0, i1 = self.list_index(strikes, s0, s1, 1)
        strikes = strikes[i0:i1]
        impl_vols = impl_vols[i0:i1]
        s0, s1 = self.two_nearby(strikes, close)
        print output % ('NEAR', 'strike0: %d(%.2f), strike1: %d(%.2f)' % (
            s0, strikes[s0], s1, strikes[s1]
        ))
        linear_iv = self.linear_expr(strikes[s0], strikes[s1], impl_vols[s0], impl_vols[s1], close)
        range_iv = self.range_expr(strikes, impl_vols, close)
        print output % ('CALC', 'linear_iv %d-day %.2f: %.2f' % (dte, close, linear_iv))
        print output % ('CALC', 'range_iv %d-day %.2f: %.2f' % (dte, close, range_iv))
        print '-' * 70

        str0, str1 = self.make_expr(impl_vols[s0], impl_vols[s1])
        cond0 = str0.format(iv0='impl_vol0', r='result', iv1='impl_vol1')
        cond1 = str1.format(linear='linear_iv', r='result')

        results = []
        for degree in range(1, 4):
            z = np.polyfit(strikes, impl_vols, degree)
            f = np.poly1d(z)
            result = round(f(close), 2)
            print output % ('CALC', 'degree: %d, impl_vol: %.2f' % (degree, result))
            arg1 = str1.format(linear=linear_iv, r=result)
            arg0 = str0.format(iv0=impl_vols[s0], r=result, iv1=impl_vols[s1])
            print output % ('COND', '%s, %s, %s' % (cond0, arg0, eval(arg0)))
            print output % ('COND', '%s, %s, %s' % (cond1, arg1, eval(arg1)))

            if eval(arg0) and eval(arg1):
                results.append(result)

        if len(results):
            poly1d_iv = round(np.mean(results), 2)
        else:
            poly1d_iv = linear_iv

        print output % ('CALC', 'poly1d_iv %d-day %.2f: %.2f' % (close, dte, poly1d_iv))
        print ''

        return range_iv, poly1d_iv, linear_iv

    def nearby_strike(self, close, days, df_date):
        """
        If close strike in strike, use direct estimate,
        get the close strike with diff dte, calc the days strike
        :param close: float
        :param days: int
        :param df_date: pd.DataFrame
        :return: float
        """
        print output % ('PROC', 'calc using nearby strike')

        dtes = np.sort(np.array(df_date['dte'].unique()))
        d0, d1 = self.two_nearby(dtes, days)
        df_near = df_date.query('dte == %d | dte == %d' % (dtes[d0], dtes[d1]))
        strikes = df_near['strike'].unique()
        s = self.nearby(strikes, close)
        df_strike = df_date.query('strike == %.2f' % strikes[s]).sort_values('dte')
        dtes = np.array(df_strike['dte'])
        impl_vols = np.array(df_strike['impl_vol'])
        print output % ('DATA', 'dte0: %d(%d), dte1: %d(%d)' % (d0, dtes[d0], d1, dtes[d1]))
        print output % ('SEED', 'index: %d, strike: %.2f, close: %.2f' % (s, strikes[s], close))

        d0, d1 = self.two_nearby(dtes, days)
        i0, i1 = self.list_index(dtes, d0, d1, 1)
        dtes = dtes[i0:i1]
        impl_vols = impl_vols[i0:i1]
        d0, d1 = self.two_nearby(dtes, days)
        linear_iv = self.linear_expr(dtes[d0], dtes[d1], impl_vols[d0], impl_vols[d1], days)
        range_iv = self.range_expr(dtes, impl_vols, days)
        print output % ('CALC', 'linear_iv for %d-days: %.2f' % (days, linear_iv))
        print output % ('CALC', 'range_iv for %d-days: %.2f' % (days, range_iv))
        print '-' * 70

        str0, str1 = self.make_expr(impl_vols[d0], impl_vols[d1])
        cond0 = str0.format(iv0='impl_vol0', r='result', iv1='impl_vol1')
        cond1 = str1.format(linear='linear_iv', r='result')

        results = []
        for degree in range(1, 4):
            z = np.polyfit(dtes, impl_vols, degree)
            f = np.poly1d(z)

            poly1d0 = round(f(days), 2)
            print output % ('CALC', 'degree: %d, poly1d_iv: %.2f' % (degree, poly1d0))

            arg0 = str0.format(iv0=impl_vols[d0], r=poly1d0, iv1=impl_vols[d1])
            arg1 = str1.format(linear=linear_iv, r=poly1d0)
            print output % ('COND', '%s, %s, %s' % (cond0, arg0, eval(arg0)))
            print output % ('COND', '%s, %s, %s' % (cond1, arg1, eval(arg1)))

            if eval(arg0) and eval(arg1):
                results.append(poly1d0)

        if len(results):
            poly1d_iv = round(np.mean(results), 2)
        else:
            poly1d_iv = linear_iv

        print output % ('CALC', 'poly1d_iv for %d-days: %.2f' % (days, poly1d_iv))
        print ''

        return range_iv, poly1d_iv, linear_iv

    def single_nearby_strike(self, close, df_date):
        """
        Calculate IV when no duplicated strike in nearby 365-days cycles
        using direct poly1d linear method to estimate approximate result
        linear_iv of final linear_iv and range_iv
        :param close: float
        :param df_date: pd.DataFrame
        :return: float
        """
        print output % ('PROC', '2 nearby strike no found, use poly1d closest')
        print output % ('SEED', 'close: %.2f' % close)
        print '-' * 70
        df_date = df_date.query('impl_vol > 0').sort_values(['dte', 'strike'])
        dtes = np.sort(df_date['dte'].unique())
        # print df_date.to_string(line_width=1000)

        results = []
        for dte in dtes:
            df_dte = df_date.query('dte == %r' % dte)
            x = np.array(df_dte['strike'])
            y = np.array(df_dte['impl_vol'])

            if len(x) == len(y) > 1:
                print output % ('SEED', 'close: %.2f, dte: %d' % (close, dte))
                if close < x[0]:
                    linear = self.linear_expr(x[0], x[1], y[0], y[1], close)
                else:
                    linear = self.linear_expr(x[-1], x[-2], y[-1], y[-2], close)

                print output % ('CALC', 'linear %d-days: %.2f' % (dte, linear))
                results.append((dte, linear))
                print '-' * 70

        x = [a for a, b in results]
        y = [b for a, b in results]
        d0, d1 = self.two_nearby(x, 365)
        for a, b in zip(x, y):
            print output % ('DATA', 'dte: %d, impl_vol: %.2f' % (a, b))

        print output % ('DATA', 'iv %d: %.2f, iv %d: %.2f' % (
            x[d0], y[d0], x[d1], y[d1]
        ))

        linear_iv = self.linear_expr(x[d0], x[d1], y[d0], y[d1], 365)
        print output % ('CALC', 'final linear_iv: %.2f' % linear_iv)

        range_iv = self.range_expr(x[d0 - 1:d1 + 2], y[d0 - 1:d1 + 2], 365)
        print output % ('CALC', 'range linear_iv: %.2f' % range_iv)

        return range_iv, linear_iv

    def single_nearby_cycle(self, close, df_date):
        """
        use every cycle to calc close price result iv to calc 365-days
        linear_iv of final linear_iv, range_iv of final linear_iv
        :param close: float
        :param df_date: pd.DataFrame
        :return: float
        """
        dtes = np.sort(np.array(df_date['dte'].unique()))
        # df_near = df_date.query('dte == %r' % dtes[-1]).sort_values('strike')
        # print df_near.to_string(line_width=1000)

        results = []
        for dte in dtes:
            print output % ('SEC', 'dte: %d' % dte)
            print '-' * 70

            df_dte = df_date.query('dte == %r & impl_vol > 0' % dte).sort_values('strike')

            # only use nearest strikes
            strikes = np.array(df_dte['strike'])
            impl_vols = np.array(df_dte['impl_vol'])
            s0, s1 = self.two_nearby(strikes, close)
            # print zip(strikes, impl_vols)
            linear_iv = self.linear_expr(strikes[s1], strikes[s0], impl_vols[s1], impl_vols[s0], close)
            range_iv = self.range_expr(strikes[s0 - 1:s1 + 2], impl_vols[s0 - 1:s1 + 2], close)
            print output % ('CALC', 'dte: %d, range_iv: %.2f' % (dte, range_iv))
            print output % ('CALC', 'dte: %d, linear_iv: %.2f' % (dte, linear_iv))
            results.append((dte, linear_iv, range_iv))
            print '-' * 70

        x = [r[0] for r in results]
        y0 = [r[1] for r in results]
        y1 = [r[2] for r in results]

        if 365 > x[-1]:
            linear_iv = self.linear_expr(x[-1], x[-2], y0[-1], y0[-2], 365)
            range_iv = self.linear_expr(x[-1], x[-2], y1[-1], y1[-2], 365)
        else:
            linear_iv = self.linear_expr(x[0], x[1], y0[0], y0[1], 365)
            range_iv = self.linear_expr(x[0], x[1], y1[0], y1[1], 365)

        print output % ('CALC', 'linear_iv in 365-days: %.2f' % linear_iv)
        print output % ('CALC', 'range_iv in 365-days: %.2f' % range_iv)

        return range_iv, linear_iv

    def multi_cycles_3d(self, close, days, df_date):
        """
        Calculate impl_vol using estimate close price strike
        in nearby cycles to form a quadratic line to estimate approximate
        process:
        1. get strike in every cycles
        2. for every cycle:
        2a. form a function using diff strike data
        2b. estimate close price iv
        3. using diff cycle close price iv in 365-days
        :param close: float
        :param days: int
        :param df_date: pd.DataFrame
        :return: float, float
        """
        print output % ('PROC', 'calc using close strike nearby cycles, same dte')
        print output % ('SEED', 'close: %.2f, days: %d' % (close, days))

        # get nearest to close price, 2 nearest 365-days cycle
        dtes = df_date['dte'].unique().astype(np.int)
        d0, d1 = self.two_nearby(dtes, days)
        i0, i1 = self.list_index(dtes, d0, d1, 1)
        dtes = dtes[i0:i1]

        results = []
        for dte in dtes:
            df_dte = df_date.query('dte == %r' % dte).sort_values('strike')
            print output % ('INIT', 'dte: %.2f, df_dte: %d' % (dte, len(df_dte)))

            strikes = np.array(df_dte['strike'])
            impl_vols = np.array(df_dte['impl_vol'])
            s0, s1 = self.two_nearby(strikes, close)
            i0, i1 = self.list_index(strikes, s0, s1, 1)
            strikes = strikes[i0:i1]
            impl_vols = impl_vols[i0:i1]
            s0, s1 = self.two_nearby(strikes, close)
            i0, i1 = self.list_index(strikes, s0, s1, 1)
            linear0 = self.linear_expr(
                strikes[s0], strikes[s1], impl_vols[s0], impl_vols[s1], close
            )
            print output % ('NEAR', 'strike0: %d(%.2f) strike1: %d(%.2f)' % (
                s0, strikes[s0], s1, strikes[s1]
            ))
            range0 = self.range_expr(strikes[i0:i1], impl_vols[i0:i1], close)
            print output % ('CALC', 'linear_iv for %d-days: %.2f' % (days, linear0))
            print output % ('CALC', 'range_iv for %d-days: %.2f' % (days, range0))
            print '-' * 70

            if impl_vols[s0] == impl_vols[s1]:
                results.append((dte, linear0, linear0, linear0, []))
                continue

            # calculate poly1d
            expr0, expr1 = self.make_expr(impl_vols[s0], impl_vols[s1])
            cond0 = expr0.format(iv0='impl_vol0', r='result', iv1='impl_vol1')
            cond1 = expr1.format(linear='linear_iv', r='result')

            poly1d_results = []
            for degree in range(1, 4):
                z = np.polyfit(strikes, impl_vols, degree)
                f = np.poly1d(z)
                errors = self.estimate_errors(f, strikes, impl_vols)
                poly1d0 = round(f(close), 2)
                print output % ('CALC', 'degree: %d, poly1d: %.2f' % (degree, poly1d0))

                arg0 = expr0.format(iv0=impl_vols[s0], r=poly1d0, iv1=impl_vols[s1])
                arg1 = expr1.format(linear=linear0, r=poly1d0)
                print output % ('COND', '%s, %s, %s' % (cond0, arg0, eval(arg0)))
                print output % ('COND', '%s, %s, %s' % (cond1, arg1, eval(arg1)))

                if eval(arg0) and eval(arg1):
                    poly1d_results.append((
                        degree, round(poly1d0, 2), round(np.std(errors), 2)
                    ))

                print '-' * 70

            if len(poly1d_results):
                poly0 = round(np.mean([p for _, p, _ in poly1d_results]), 2)
            else:
                poly0 = linear0

            results.append((dte, linear0, range0, poly0, poly1d_results))

        print output % ('DONE', 'finish calc strike %.2f in every dte' % close)
        print '-' * 70

        for dte, linear0, range0, poly1d_iv, poly1d_results in results:
            print output % ('DATA', 'dte: %d, linear_iv: %.2f, range_iv: %.2f' % (
                dte, linear0, range0
            ))
            for degree, poly0, errors in poly1d_results:
                print output % ('DATA', 'degree: %d, poly1d: %.2f, errors: %.2f' % (
                    degree, poly0, errors
                ))

        print '-' * 70
        print output % ('INIT', 'start calc iv using results')
        print '-' * 70

        d0, d1 = self.two_nearby(dtes, days)
        i0, i1 = self.list_index(dtes, d0, d1, 1)
        print output % ('NEAR', 'dte0: %d(%d), dte1: %d(%d)' % (d0, dtes[d0], d1, dtes[d1]))

        linear_ivs = [iv for _, iv, _, _, _ in results]
        range_ivs = [iv for _, _, iv, _, _ in results]
        poly1d_ivs = [iv for _, _, _, iv, _ in results]
        print output % ('DATA', 'dtes: %s' % dtes)
        print output % ('DATA', 'linear: %s' % linear_ivs)
        print output % ('DATA', 'range: %s' % range_ivs)
        print output % ('DATA', 'poly1d: %s' % poly1d_ivs)

        linear_iv = self.linear_expr(dtes[d0], dtes[d1], linear_ivs[d0], linear_ivs[d1], days)
        range_iv = self.range_expr(dtes[i0:i1], range_ivs[i0:i1], days)
        z = np.polyfit(dtes, poly1d_ivs, 1)
        f = np.poly1d(z)
        poly1d_iv = round(f(days), 2)
        print output % ('CALC', 'range_iv 365-days: %.2f' % range_iv)
        print output % ('CALC', 'poly1d_iv 365-days: %.2f' % poly1d_iv)
        print output % ('CALC', 'linear_iv 365-days: %.2f' % linear_iv)
        print ''

        return range_iv, poly1d_iv, linear_iv

    def multi_strikes_3d(self, close, days, df_date):
        """
        Calculate impl_vol using 2 nearby diff dte strike data
        to form a quadratic line to estimate approximate result, process:
        1. get 2 nearby strikes
        2. for each strike
        2a. form poly for diff dte into function
        2b. estimate 365-days result for strike
        3. using 2 strikes result, estimate close price iv
        :param close: float
        :param days: int
        :param df_date: pd.DataFrame
        :return: float, float, float
        """
        print output % ('PROC', 'calc using two nearby strike, diff dte')
        print output % ('CLOSE', 'close: %.2f, days: %d' % (close, days))
        print '-' * 70

        cycles = np.array(df_date['dte'].unique())
        c0, c1 = self.two_nearby(cycles, days)
        print output % ('NEAR', 'dte0: %d(%d), dte1: %d(%d)' % (c0, cycles[c0], c1, cycles[c1]))

        print output % ('DATA', 'use strike exists in both dtes')
        df_cycles = df_date.query('dte == %d | dte == %d' % (cycles[c0], cycles[c1]))
        counts = df_cycles['strike'].value_counts()
        strikes = np.sort(counts[counts == 2].index)

        s0, s1 = self.two_nearby(strikes, close)
        print output % ('NEAR', 'strike0: %d(%.2f), strike1: %d(%.2f)' % (
            s0, strikes[s0], s1, strikes[s1]
        ))

        # reduce size of strikes
        i0, i1 = self.list_index(strikes, s0, s1, 1)
        strikes = strikes[i0:i1]
        print '-' * 70

        results = []
        for strike in strikes:
            df_strike = df_date.query('strike == %r' % strike).sort_values('dte')
            print output % ('INIT', 'strike: %.2f, df_strike: %d' % (strike, len(df_strike)))

            dtes = np.array(df_strike['dte'])
            impl_vols = np.array(df_strike['impl_vol'])
            d0, d1 = self.two_nearby(dtes, days)
            i0, i1 = self.list_index(dtes, d0, d1, 1)
            dtes = dtes[i0:i1]
            impl_vols = impl_vols[i0:i1]
            print output % ('DATA', 'dtes: %s' % dtes)

            d0, d1 = self.two_nearby(dtes, days)
            linear0 = self.linear_expr(dtes[d0], dtes[d1], impl_vols[d0], impl_vols[d1], days)
            range0 = self.range_expr(dtes, impl_vols, days)
            print output % ('CALC', 'linear_iv for %.2f: %.2f' % (strike, linear0))
            print output % ('CALC', 'range_iv for %.2f: %.2f' % (strike, range0))
            print '-' * 70

            if impl_vols[d0] == impl_vols[d1]:
                results.append((strike, linear0, linear0, linear0, []))
                continue

            # make expression
            expr0, expr1 = self.make_expr(impl_vols[d0], impl_vols[d1])
            cond0 = expr0.format(iv0='impl_vol0', r='result', iv1='impl_vol1')
            cond1 = expr1.format(linear='linear_iv', r='result')

            # calculate poly1d
            poly1d_results = []
            for degree in range(1, 4):
                z = np.polyfit(dtes, impl_vols, degree)
                f = np.poly1d(z)
                r = round(f(days), 2)

                print output % ('CALC', 'degree: %d, poly1d_iv for %.2f: %.2f' % (
                    degree, strike, r
                ))

                errors = self.estimate_errors(f, dtes, impl_vols)

                # condition section
                arg0 = expr0.format(iv0=impl_vols[d0], r=r, iv1=impl_vols[d1])
                arg1 = expr1.format(linear=linear0, r=r)
                print output % ('COND', '%s, %s, %s' % (cond0, arg0, eval(arg0)))
                print output % ('COND', '%s, %s, %s' % (cond1, arg1, eval(arg1)))

                if eval(arg0) and eval(arg1):
                    poly1d_results.append((
                        degree, r, round(np.std(errors), 2)
                    ))

                print '-' * 70

            if len(poly1d_results):
                poly0 = round(np.mean([iv for _, iv, _ in poly1d_results]), 2)
            else:
                poly0 = linear0

            results.append((
                strike, range0, linear0, poly0, poly1d_results
            ))

        for strike, l, r, p, poly1d_results in results:
            print output % ('DATA', 'strike: %.2f, linear: %.2f, range: %.2f, poly1d: %.2f' % (
                strike, l, r, p
            ))
            for degree, poly0, errors in poly1d_results:
                print output % ('DATA', 'degree: %d, poly1d: %.2f, errors: %.2f' % (
                    degree, poly0, errors
                ))

        print '-' * 70
        print output % ('INIT', 'start calc iv using results')
        print '-' * 70

        print output % ('DATA', 'close: %.2f' % close)

        strikes = np.array([s for s, _, _, _, _ in results])
        linear_ivs = np.array([iv for _, iv, _, _, _ in results])
        range_ivs = np.array([iv for _, _, iv, _, _ in results])
        poly1d_ivs = np.array([iv for _, _, _, iv, _ in results])

        s0, s1 = self.two_nearby(strikes, close)
        i0, i1 = self.list_index(strikes, s0, s1, 1)
        z = np.polyfit(strikes, poly1d_ivs, 2)
        f = np.poly1d(z)

        linear_iv = self.linear_expr(strikes[s0], strikes[s1], linear_ivs[s0], linear_ivs[s1], close)
        range_iv = self.range_expr(strikes[i0:i1], range_ivs[i0:i1], close)
        poly1d_iv = round(f(close), 2)

        print output % ('CALC', 'linear_iv for %.2f: %.2f' % (close, linear_iv))
        print output % ('CALC', 'range_iv for %.2f: %.2f' % (close, range_iv))
        print output % ('CALC', 'poly1d_iv for %.2f: %.2f' % (close, poly1d_iv))

        return range_iv, poly1d_iv, linear_iv

    def calc_by_days(self, days):
        """
        Loop each date and select calculate method
        the run calc for certain days
        :param days: int
        :return:
        """
        results = []
        for index, data in self.df_stock.iterrows():
            action = ''

            close = data['close']
            df_date = self.df_all.query('date == %r & name == "CALL"' % index)

            # if have not 100 right, remove duplicate split data
            df_date = self.format_data(df_date)
            """:type: pd.DataFrame"""

            print output % ('LOOP', 'date: %s, close: %.2f' % (index.strftime('%Y-%m-%d'), close))

            if len(df_date) == 0:
                print output % ('ERROR', 'date have no options: %s' % index.strftime('%Y-%m-%d'))
                continue

            dtes = np.sort(np.array(df_date['dte'].unique()))
            d0, d1 = self.two_nearby(dtes, days)
            df_dte = df_date.query('dte == %r | dte == %r' % (dtes[d0], dtes[d1]))
            strikes = np.sort(df_dte[df_dte.duplicated('strike')]['strike'])
            strike = 0

            if 363 < dtes[d0] < 367 or 363 < dtes[d1] < 367:
                s0, s1 = self.two_nearby(strikes, close)
                if s0 == s1:
                    action = 'single_strike'
                else:
                    action = 'nearby_dte'
            elif d0 == d1:
                action = 'single_dte'
            else:
                if len(strikes) == 0:
                    # no similar strike found, use closest
                    action = 'no_dup_strike'
                else:
                    s0, s1 = self.two_nearby(strikes, close)

                    s = self.nearby(strikes, close)
                    if close - 0.11 < strikes[s] < close + 0.11:
                        action = 'nearby_strike'
                        strike = strikes[s]
                    elif s0 == s1:
                        action = 'single_strike'
                        strike = strikes[s0]

            print '-' * 70
            if action == 'nearby_dte':
                print output % ('EXIST', 'nearby 365-days in dtes: %d %d' % (dtes[d0], dtes[d1]))
                print '-' * 70
                range_iv, poly1d_iv, linear_iv = self.nearby_365days(close, dtes[d0], df_date)
            elif action == 'single_dte':
                print output % ('WARN', 'single nearby DTE cycle found: %d' % dtes[d0])
                print '-' * 70
                range_iv, linear_iv = self.single_nearby_cycle(close, df_date)
                poly1d_iv = linear_iv
            elif action in ('no_dup_strike', 'single_strike'):
                if action == 'single_strike':
                    print output % ('WARN', 'single nearby STRIKE found: %.2f' % strike)
                    print '-' * 70
                else:
                    print output % ('WARN', 'no dup STRIKE found both cycles')
                    print '-' * 70

                range_iv, linear_iv = self.single_nearby_strike(close, df_date)
                poly1d_iv = linear_iv
            elif action == 'nearby_strike':
                print output % ('EXIST', 'nearby %.2f price found in strike: %.2f' % (close, strike))
                print '-' * 70
                range_iv, poly1d_iv, linear_iv = self.nearby_strike(close, days, df_date)
            else:
                print output % ('NORM', '2-nearby-cycles, 2-nearby-strikes found')
                print output % ('NORM', 'using normal 3d calculation')
                print '-' * 70
                range_iv0, poly1d_iv0, linear_iv0 = self.multi_cycles_3d(close, days, df_date)
                range_iv1, poly1d_iv1, linear_iv1 = self.multi_strikes_3d(close, days, df_date)
                range_iv = np.mean([range_iv0, range_iv1])
                poly1d_iv = np.mean([poly1d_iv0, poly1d_iv1])
                linear_iv = np.mean([linear_iv0, linear_iv1])

            print '-' * 70

            results.append({
                'date': index,
                'range_iv': range_iv,
                'poly1d_iv': poly1d_iv,
                'linear_iv': linear_iv,
            })

















