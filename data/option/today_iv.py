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
            else:
                iv1 = self.linear_expr(x[0], x[1], y[0], y[1], base)
                iv2 = y[1] - (y[2] - y[1]) / (x[2] - x[1]) * (x[1] - base)
                results = [iv1, iv2]
        else:
            iv0 = y[1] + (y[1] - y[0]) / (x[1] - x[0]) * (base - x[1])
            iv1 = self.linear_expr(x[1], x[2], y[1], y[2], base)
            iv2 = y[2] - (y[3] - y[2]) / (x[3] - x[2]) * (x[2] - base)
            results = [iv0, iv1, iv2]

        return round(np.mean(results), 2)

    @staticmethod
    def make_cond(a, b):
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
    def remove_split(df_date):
        """

        :param df_date:
        :return:
        """
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

    def nearby_365days(self, close, dte, df_date, plot=False):
        """
        If 365-days in dte, use direct estimate,
        get the 365-days cycles, calculate the close price strike
        :param close: float
        :param dte:
        :param df_date: pd.datetime
        :type plot: bool
        :return: float, float
        """
        print output % ('PROC', '365-days exists in dte cycle, direct process')

        df_dte = df_date.query('dte == %r' % dte).sort_values('strike')
        print output % ('SEED', 'close: %.2f' % close)
        # print df_date.to_string(line_width=1000)

        # find nearest
        strikes = np.array(df_dte['strike'])
        impl_vols = np.array(df_dte['impl_vol'])
        s0, s1 = self.two_nearby(strikes, close)
        print output % ('NEAR', 'strike0: %d(%.2f), strike1: %d(%.2f)' % (
            s0, strikes[s0], s1, strikes[s1]
        ))
        linear_iv = self.linear_expr(strikes[s0], strikes[s1], impl_vols[s0], impl_vols[s1], close)
        range_iv = self.range_expr(strikes[s0 - 1:s1 + 2], impl_vols[s0 - 1:s1 + 2], close)
        print '-' * 70
        print output % ('CALC', 'linear_iv: %.2f' % linear_iv)
        print output % ('CALC', 'range_iv: %.2f' % range_iv)
        print '-' * 70

        x = []
        y = []
        last = max(df_dte['impl_vol']) + 1
        for strike, impl_vol in zip(df_dte['strike'], df_dte['impl_vol']):
            print output % ('CHECK', 'ready x, y in quadratic: %.2f %.2f' % (strike, impl_vol))
            if strike in (strikes[s0], strikes[s1]):
                x.append(strike)
                y.append(round(impl_vol, 2))
                last = impl_vol
            elif last > impl_vol:
                x.append(strike)
                y.append(round(impl_vol, 2))
                last = impl_vol

        print output % ('CLEAN', 'only use nearest 6 data')
        s0, s1 = self.two_nearby(x, close)
        x = x[s0 - 4:s1 + 1]
        y = y[s0 - 4:s1 + 1]
        for a, b in zip(x, y):
            print output % ('DATA', 'strike: %.2f, impl_vol: %.2f' % (a, b))

        # start calc linear iv

        i0, i1 = self.two_nearby(x, close)
        print output % ('NEAR', 'index0: %d(%.2f), index1: %d(%.2f)' % (i0, x[i0], i1, x[i1]))

        # start calc poly1d iv
        results = []
        keep_calc = True
        while keep_calc:
            for degree in range(1, 4):
                z = np.polyfit(x, y, degree)
                f = np.poly1d(z)
                result = round(f(close), 2)
                print output % ('CALC', 'degree: %d, impl_vol: %.2f' % (degree, result))
                str0, str1 = self.make_cond(y[i0], y[i1])
                cond0 = str0.format(iv0='impl_vol0', r='result', iv1='impl_vol1')
                arg0 = str0.format(iv0=y[i0], r=result, iv1=y[i1])
                cond1 = str1.format(linear='linear_iv', r='result')
                arg1 = str1.format(linear=linear_iv, r=result)

                print output % ('COND', '%s, %s, %s' % (cond0, arg0, eval(arg0)))
                print output % ('COND', '%s, %s, %s' % (cond1, arg1, eval(arg1)))

                if eval(arg0) and eval(arg1):
                    results.append(result)

            if len(results):
                keep_calc = False
            else:
                print output % ('PROC', 'reduce sample size to nearest')
                x = x[1:]
                y = y[1:]
                i0, i1 = self.two_nearby(x, close)
                print output % ('NEAR', 'index0: %d(%.2f), index1: %d(%.2f)' % (
                    i0, x[i0], i1, x[i1]
                ))

                if len(x) < 3:
                    print output % ('ERROR', 'not enough data for poly1d')
                    keep_calc = False

                print '-' * 70

        if len(results):
            poly1d_iv = round(np.mean(results), 2)
        else:
            poly1d_iv = linear_iv

        print output % ('CALC', 'poly1d_iv: %.2f' % poly1d_iv)

        if plot:
            x.append(close)
            y.append(poly1d_iv)
            z = np.polyfit(x, y, 2)
            f = np.poly1d(z)
            x_new = np.linspace(x[0], x[-1], 50)
            y_new = f(x_new)

            plt.plot(x, y, 'o', x_new, y_new)
            plt.xlim([x[0] - 1, x[-1] + 1])
            plt.show()

        return range_iv, poly1d_iv, linear_iv

    def nearby_strike(self, date, df_date, plot=False):
        """
        If close strike in strike, use direct estimate,
        get the close strike with diff dte, calc the 365-days strike
        :param date: pd.datetime
        :param df_date: pd.DataFrame
        :param plot: bool
        :return: float
        """
        close = self.df_stock.ix[date]['close']

        dtes = np.sort(np.array(df_date['dte'].unique()))
        # print df_date['dte'].unique()
        d0, d1 = self.two_nearby(dtes, 365)
        print output % ('DATA', 'dte0: %d(%d), dte1: %d(%d)' % (d0, dtes[d0], d1, dtes[d1]))
        df_near = df_date.query('dte == %d | dte == %d' % (dtes[d0], dtes[d1]))
        # print df_near.sort_values('impl_vol').to_string(line_width=1000)

        strikes = np.sort(df_near['strike'].unique())
        s = self.nearby(strikes, close)

        print output % ('SEED', 'index: %d, strike: %.2f, close: %.2f' % (s, strikes[s], close))
        df_strike = df_date.query('strike == %.2f' % strikes[s]).sort_values('dte')
        # print df_strike.to_string(line_width=1000)

        x = []
        y = []
        last = max(df_strike['impl_vol']) + 1
        for dte, impl_vol in zip(df_strike['dte'], df_strike['impl_vol']):
            if last > impl_vol:
                print output % ('CHECK', 'smooth dte: %d, impl_vol: %.2f' % (dte, impl_vol))
                x.append(dte)
                y.append(round(impl_vol, 2))
                last = impl_vol

        d0, d1 = self.two_nearby(x, 365)
        linear_iv = round(y[d0] + (
            (y[d1] - y[d0]) / float(x[d1] - x[d0]) * (365 - x[d0])
        ), 2)

        print output % ('CALC', 'linear_iv 365-days: %.2f' % linear_iv)

        str0, str1 = self.make_cond(y[d0], y[d1])
        cond0 = str0.format(iv0='impl_vol0', r='result', iv1='impl_vol1')
        cond1 = str1.format(linear='linear_iv', r='result')
        print '-' * 70

        results = []
        for degree in range(1, 4):
            z = np.polyfit(x, y, degree)
            f = np.poly1d(z)

            result = round(f(365), 2)
            print output % ('CALC', 'degree: %d, poly1d_iv for 365-days: %.2f' % (degree, result))
            results.append(result)

            arg0 = str0.format(iv0=y[d0], r=result, iv1=y[d1])
            arg1 = str1.format(linear=linear_iv, r=result)
            print output % ('COND', '%s, %s, %s' % (cond0, arg0, eval(arg0)))
            print output % ('COND', '%s, %s, %s' % (cond1, arg1, eval(arg1)))

            if plot:
                # calculate new x's and y's
                x.append(365)
                y.append(result)
                x_new = np.linspace(x[0], x[-1], 50)
                y_new = f(x_new)
                plt.plot(x, y, 'o', x_new, y_new)
                plt.xlim([x[0] - 1, x[-1] + 1])
                plt.show()

                x.pop()
                y.pop()

        print '-' * 70
        print output % ('CALC', 'linear_iv in %.2f: %.2f' % (close, linear_iv))

        if len(results):
            poly1d_iv = round(np.mean(results), 2)
        else:
            poly1d_iv = linear_iv

        print output % ('CALC', 'poly1d_iv in %.2f: %.2f' % (close, poly1d_iv))

        s0, s1 = self.two_nearby(x, 365)
        print output % ('NEAR', 'strike0: %d(%.2f), strike1: %d(%.2f)' % (s0, x[s0], s1, x[s1]))
        range_iv = self.range_expr(x[s0 - 1:s1 + 2], y[s0 - 1:s1 + 2], 365)
        print output % ('CALC', 'range_iv: %.2f' % range_iv)

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
            print output % ('SEED', 'close: %.2f, dte: %d' % (close, dte))

            df_dte = df_date.query('dte == %r' % dte)
            x = np.array(df_dte['strike'])
            y = np.array(df_dte['impl_vol'])

            # smooth data
            data = []
            last = min(y) - 1 if y[0] < y[-1] else max(y) + 1
            cond = '{last} < {b}' if y[0] < y[-1] else '{last} > {b}'
            for a, b in zip(x, y):
                if eval(cond.format(last=last, b=b)):
                    print output % ('CHECK', 'smooth strike: %.2f, impl_vol: %.2f' % (a, b))
                    data.append((a, b))
                    last = b

            x = [a for a, b in data]
            y = [b for a, b in data]

            if close < x[0]:
                linear = self.linear_expr(x[0], x[1], y[0], y[1], close)
            else:
                linear = self.linear_expr(x[-1], x[-2], y[-1], y[-2], close)

            print output % ('CALC', 'linear %d-days: %.2f' % (dte, linear))
            results.append((dte, linear))
            print '-' * 70

        x = [a for a, b in results]
        y = [b for a, b in results]
        d0, d1 = self.two_nearby(dtes, 365)
        print x
        print y
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

    def get_cycle_data(self, date):
        """
        Supply x, y cycle data for calc_cycle
        :param date: str
        :return: float, list, dict
        """
        # get stock close price
        close = self.df_stock.ix[date]['close']

        # get options
        df_date = self.df_all.query(
            'date == %r & name == "CALL"' % date
        ).sort_values('dte')

        # get nearest to close price, 2 nearest 365-days cycle
        # print df_date.to_string(line_width=1000)
        dtes = df_date['dte'].unique().astype(np.int)
        # same date, diff dte, diff strike, for 2 cycles
        c = self.nearby(dtes, 365)
        start, stop = 3, 3
        start = c - start if c - start > -1 else 0
        stop = c + stop if c + stop <= len(dtes) else len(dtes)
        cycles = dtes[start:stop]

        df_cycles = []
        for dte in cycles:
            print output % (
                'QUERY', 'get df_cycle: %d' % dte
            )
            df_cycle = df_date.query('dte == %r' % dte).sort_values('strike')
            df_cycles.append(df_cycle)
            # print df_cycle.to_string(line_width=1000)

        # put into x, y then keep impl_vol smooth
        data = {dte: [] for dte in cycles}
        for dte, df_temp in zip(cycles, df_cycles):
            print output % ('CHECK', 'ready x, y data that move quadratic: %d' % dte)
            last = max(df_temp['impl_vol'] + 1)
            for strike, impl_vol in zip(df_temp['strike'], df_temp['impl_vol']):
                # print strike, impl_vol, last, last > impl_vol > 0
                if last > impl_vol > 0:
                    # print strike, impl_vol
                    last = impl_vol
                    data[dte].append((strike, round(impl_vol, 2)))

        # only use nearest 10 or less
        print output % ('PROC', 'reduce sample size to nearest')
        for dte in cycles:
            index = self.nearby([d0 for d0, d1 in data[dte]], close)
            start, stop = 5, 5
            start = index - start if index - start > -1 else 0
            stop = index + stop if index + stop <= len(data[dte]) else len(data[dte])
            print output % (
                'SIZE', 'dte: %d, index: %d, pos: -%d, +%d, len: %d -> %d' % (
                    dte, index, start, stop, len(data[dte]), len(data[dte][start:stop])
                )
            )
            data[dte] = data[dte][start:stop]

        print '-' * 70

        return close, cycles, data

    # todo: cont here

    def calc_cycles(self, date, plot=False):
        """
        Calculate impl_vol using estimate close price strike
        in nearby cycles to form a quadratic line to estimate approximate
        process:
        1. get strike in every cycles
        2. for every cycle:
        2a. form a function using diff strike data
        2b. estimate close price iv
        3. using diff cycle close price iv in 365-days
        :param date: pd.datetime
        :param plot: bool
        :return: (float, float)
        """
        print output % ('PROC', 'calc using close strike nearby cycles, same dte')
        close, cycles, data = self.get_cycle_data(date)

        results = {c: [] for c in cycles}
        for cycle in cycles:
            print output % ('INIT', 'cycle: %.2f' % cycle)
            print '-' * 70
            x = [a for a, b in data[cycle]]
            y = [b for a, b in data[cycle]]

            # calculate polynomial
            keep_calc = True
            while keep_calc:
                for a, b in zip(x, y):
                    print output % ('DATA', 'strike: %.2f, impl_vol: %.2f' % (
                        a, b
                    ))
                print '-' * 70
                for degree in range(1, 4):
                    z = np.polyfit(x, y, degree)
                    f = np.poly1d(z)

                    errors = []
                    for a, b in data[cycle]:
                        # print a, b, '%.2f' % f(a), '%.2f' % (f(a) - b)
                        errors.append(round(f(a) - b, 2))

                    i0, i1 = self.nearby(x, close), self.nearby(x, close, True)
                    i0, i1 = sorted([i0, i1])
                    result = round(f(close), 2)
                    print output % (
                        'SEED',
                        'close: %.2f, cycle: %.2f, degree: %d' % (close, cycle, degree)
                    )
                    print output % (
                        'ERROR', errors[1:-1]
                    )
                    print output % (
                        'CALC',
                        'ImplVol: %.2f' % result
                    )
                    print output % (
                        'COND',
                        'strike0 > price > strike1? %.2f > %.2f > %.2f? %s' % (
                            y[i0], result, y[i1], y[i0] > result > y[i1]
                        )
                    )
                    # print zip(x, y)
                    dif = round((y[i0] - y[i1]) / float(x[i0] - x[i1]) * (x[i0] - close), 2)
                    linear = y[i0] - dif
                    print output % (
                        'CALC', 'linear: %.2f' % linear
                    )
                    print output % (
                        'COND', 'linear > poly? %.2f >= %.2f? %s' % (linear, result, linear >= result)
                    )

                    if y[i0] > result > y[i1] and linear >= result:
                        results[cycle].append({
                            'degree': degree,
                            'poly1d': round(result, 2),
                            'linear': round(linear, 2),
                            'errors': round(np.std(errors), 2),
                        })
                        keep_calc = False
                        print output % ('DONE', 'found')

                    print '-' * 70

                    # method not found, reduce sample size
                if keep_calc:
                    x = x[1:len(x)]
                    y = y[1:len(y)]
                    i0, i1 = self.nearby(x, close), self.nearby(x, close, True)
                    i0, i1 = sorted([i0, i1])
                    print output % ('CONT', 'result not found, reduce 1 sample')
                    print output % ('NEAR', 'dte: (%d)%d - (%d)%d' % (i0, x[i0], i1, x[i1]))

                    if x[0] > close:
                        # unable to found
                        print output % ('ERROR', 'not enough data for poly1d')
                        fill_value = round((linear + y[i0]) / 2.0, 2)
                        results[cycle].append({
                            'degree': 0,
                            'poly1d': fill_value,
                            'linear': round(linear, 2),
                            'errors': 0,
                        })
                        print output % ('FILL', 'using below linear value: %.2f' % fill_value)

                        break

                    print '.' * 70

        print output % ('DONE', 'finish calc strike %.2f in every dte' % close)
        print '-' * 70

        for key in results.keys():
            print output % ('DATA', 'result for dte: %.2f in strike: %.2f' % (key, close))
            for r in results[key]:
                print output % ('DATA', 'degree: %d, errors: %.2f, linear: %.2f, poly1d: %.2f' % (
                    r['degree'], r['errors'], r['linear'], r['poly1d'],
                ))

        print '-' * 70
        print output % ('INIT', 'start calc iv using results')
        print '-' * 70

        # now lets use result data to generate 365 data
        print output % ('SEED', 'stock price: %.2f' % close)
        index0, index1 = [(d0, d1) for d0, d1 in zip(cycles[:-1], cycles[1:]) if d0 < 365 < d1][0]
        print output % ('SEED', 'dte0: %d, dte1: %d' % (index0, index1))
        cycle0_iv = round(np.mean([d['poly1d'] for d in results[index0]]), 2)
        cycle1_iv = round(np.mean([d['poly1d'] for d in results[index1]]), 2)

        # use linear
        print output % ('SEED', 'cycle0_iv: %.2f, cycle1_iv: %.2f' % (cycle0_iv, cycle1_iv))
        linear_iv = round(cycle0_iv + (
            (cycle1_iv - cycle0_iv) / float(index1 - index0) * (365 - index0)
        ), 2)
        print output % ('CALC', 'linear iv: %.2f' % linear_iv)

        # use polyfit
        x = []
        y = []
        for dte in sorted(results.keys()):
            x.append(dte)
            impl_vol = round(np.mean([d['poly1d'] for d in results[dte]]), 2)
            y.append(impl_vol)
            print output % ('DATA', 'dte: %.2f, impl_vol: %.2f' % (dte, impl_vol))

        print output % ('NOTE', 'poly1d estimate each cycle in price: %.2f' % close)

        poly1d_results = []
        for degree in range(1, 4):
            z = np.polyfit(x, y, degree)
            f = np.poly1d(z)
            result = round(f(365), 2)
            print output % ('SEED', 'degree: %d' % degree)
            print output % ('CALC', 'close: %.2f in 365-days: %.2f' % (close, result))

            if result > linear_iv:
                poly1d_results.append(result)
        else:
            if not len(poly1d_results):
                poly1d_iv = round((linear_iv + cycle1_iv) / 2.0, 2)
                print output % ('FILL', 'poly1d result not found, fill: %.2f' % poly1d_iv)
            else:
                poly1d_iv = float(np.mean(poly1d_results))
                print output % ('CALC', 'final poly1d_iv: %.2f' % poly1d_iv)

        # calculate polynomial
        if plot:
            # calculate new x's and y's
            x.append(365)
            y.append(poly1d_iv)
            x = sorted(x)
            y = sorted(y)
            z = np.polyfit(x, y, 2)
            f = np.poly1d(z)
            x_new = np.linspace(x[0], x[-1], 50)
            y_new = f(x_new)

            plt.plot(x, y, 'o', x_new, y_new)
            plt.xlim([x[0] - 1, x[-1] + 1])
            plt.show()

        print ''

        return poly1d_iv, linear_iv

    def calc_strikes(self, date, plot=False):

        """
        Calculate impl_vol using 2 nearby diff dte strike data
        to form a quadratic line to estimate approximate result
        process:
        1. get 2 nearby strikes
        2. for each strike
        2a. form poly for diff dte into function
        2b. estimate 365-days result for strike
        3. using 2 strikes result, estimate close price iv
        :param date: str
        :param plot: bool
        :return: (float, float)
        """
        print output % ('PROC', 'calc using two nearby strike, diff dte')
        print '-' * 70
        print output % ('DATE', 'date: %s' % date.strftime('%Y-%m-%d'))

        # get stock close price
        close = self.df_stock.ix[date]['close']
        print output % ('CLOSE', 'using: %.2f' % close)

        # get options
        df_date = self.df_all.query(
            'date == %r & name == "CALL" & others == ""' % date
        ).sort_values('dte')
        # print df_date.query('strike == 60').to_string(line_width=1000)

        strikes = {}
        dtes = df_date['dte'].unique()
        for dte in dtes:
            df_dte = df_date.query('dte == %r' % dte)
            strikes[dte] = df_dte['strike'].unique()

        line = []
        for s in strikes.values():
            # print s
            line += list(s)

        # print line
        values = pd.Series(line).value_counts()
        strikes = values[values == len(dtes)].index.sort_values()
        # print strikes

        s0 = self.nearby(strikes, close)
        s1 = self.nearby(strikes, close, True)
        s0, s1 = sorted([s0, s1])
        print output % ('DATA', 'strike: %.2f to %.2f' % (s0, s1))
        print '-' * 70
        start = s0 - 3 if s0 - 3 > -1 else 0
        stop = s1 + 2 if s1 + 2 < len(strikes) else len(strikes)
        strikes = strikes[start:stop]
        print strikes

        results = {s: [] for s in strikes}
        for strike in strikes:
            print output % ('INIT', 'strike: %.2f' % strike)
            print '-' * 70

            df_strike = df_date.query('strike == %r' % strike).sort_values('dte')

            # find nearest
            dtes = np.array(df_strike['dte'])
            d0 = self.nearby(dtes, 365)
            d1 = self.nearby(dtes, 365, True)
            d0, d1 = sorted([d0, d1])

            # smooth impl_vol
            temp = np.array(df_strike['impl_vol'])
            x = []
            y = []
            last = max(temp) + 1
            for k, (d, s) in enumerate(zip(dtes, temp)[::-1]):
                print output % ('CHECK', 'ready x, y smooth quadratic data: %d' % d)
                if not s:
                    continue

                if len(temp) - k in (d0, d1):
                    x.append(d)
                    y.append(round(s, 2))
                    last = s
                elif s < last:
                    x.append(d)
                    y.append(round(s, 2))
                    last = s
            else:
                x = sorted(x)
                y = sorted(y)
            print '-' * 70

            print zip(x, y)

            x = sorted(x)
            y = sorted(y)
            d0 = self.nearby(x, 365)
            d1 = self.nearby(x, 365, True)
            d0, d1 = sorted([d0, d1])

            print output % ('NEAR', 'dte: (%d)%d - (%d)%d' % (d0, x[d0], d1, x[d1]))
            print output % ('DATA', '[... %s ...]' % ', '.join(
                ['(%d, %.2f)' % (s[0], s[1]) for s in zip(x, y)[d0:d1 + 1]]
            ))

            # calc linear iv
            linear_iv0 = round(y[d0] + (
                (y[d1] - y[d0]) / float(x[d1] - x[d0]) * (365 - x[d0])
            ), 2)
            print output % ('CALC', 'linear  IV: %.2f' % linear_iv0)

            # calculate polynomial
            keep_calc = True
            while keep_calc:
                for degree in range(1, 4):
                    print output % ('SEED', 'degree: %d' % degree)
                    z = np.polyfit(x, y, degree)
                    f = np.poly1d(z)
                    polyfit_iv0 = round(f(365), 2)
                    print output % ('CALC', 'polyfit IV: %.2f' % polyfit_iv0)
                    print output % (
                        'COND', 'iv0 < result_iv0 < iv1, %.2f < %.2f < %.2f, %s' % (
                            y[d0], polyfit_iv0, y[d1], y[d0] < polyfit_iv0 < y[d1]
                        )
                    )
                    print output % (
                        'COND', 'result_iv0 > linear_iv0, %.2f > %.2f, %s' % (
                            polyfit_iv0, linear_iv0, polyfit_iv0 > linear_iv0
                        )
                    )

                    errors = []
                    for a, b in zip(x, y):
                        # print a, b, '%.2f' % f(a), '%.2f' % (f(a) - b)
                        errors.append(round(f(a) - b, 2))

                    print output % ('ERROR', '[%s%s]' % (
                        ', '.join(['%.2f' % e for e in errors[:8]]), '...' if len(errors) > 8 else ''
                    ))

                    if y[d0] < polyfit_iv0 < y[d1] and polyfit_iv0 > linear_iv0:
                        results[strike].append({
                            'degree': degree,
                            'poly1d': round(polyfit_iv0, 2),
                            'linear': round(linear_iv0, 2),
                            'errors': round(np.std(errors), 2)
                        })
                        keep_calc = False

                        # calculate new x's and y's
                        if plot:
                            x_new = np.linspace(x[0], x[-1], 50)
                            y_new = f(x_new)
                            plt.plot(x, y, 'o', x_new, y_new)
                            plt.xlim([x[0] - 1, x[-1] + 1])
                            plt.show()

                    print '-' * 70

                # method not found, reduce sample size
                if keep_calc:
                    x = x[1:len(x)]
                    y = y[1:len(y)]
                    d0 -= 1
                    d1 -= 1

                    try:
                        print output % ('CONT', 'result not found, reduce 1 sample')
                        print output % ('NEAR', 'dte: (%d)%d - (%d)%d' % (d0, x[d0], d1, x[d1]))

                        if len(x) < d1:
                            # unable to found
                            print output % ('ERROR', 'not enough data')
                            break

                        print '.' * 70
                    except IndexError:
                        results[strike].append({
                            'degree': 0,
                            'poly1d': round(linear_iv0, 2),
                            'linear': round(linear_iv0, 2),
                            'errors': 0
                        })

                        break

        print output % ('DONE', 'finish calc 2 nearby strikes in diff dte')
        print '-' * 70

        # now estimate approximate IV
        # pprint(results)
        for key in sorted(results.keys()):
            print output % ('SEED', 'result for strike: %.2f in 365-days' % key)
            for r in results[key]:
                print output % ('SEED', 'degree: %d, errors: %.2f, linear: %.2f, poly1d: %.2f' % (
                    r['degree'], r['errors'], r['linear'], r['poly1d'],
                ))

        print '-' * 70
        print output % ('INIT', 'start calc iv using results')
        print '-' * 70

        print output % ('DATA', 'close: %.2f' % close)

        # calculate linear result using poly1d
        print '-' * 70
        print output % ('SEC', 'calculate linear iv using poly1d')
        print '-' * 70

        linear_x = sorted(results.keys())
        linear_y = np.array([np.mean([i['linear'] for i in results[k]]) for k in linear_x])
        for strike, impl_vol in zip(linear_x, linear_y):
            print output % ('DATA', 'strike: %.2f, impl_vol: %.2f' % (strike, impl_vol))

        s0 = self.nearby(linear_x, close)
        s1 = self.nearby(linear_x, close, True)
        s0, s1 = sorted([s0, s1])
        print output % ('NEAR', '%.2f(%.2f), %.2f(%.2f)' % (
            linear_x[s0], linear_y[s0], linear_x[s1], linear_y[s1]
        ))
        linear_iv = round(linear_y[s0] + (
            (linear_y[s1] - linear_y[s0]) / float(linear_x[s1] - linear_x[s0]) *
            (close - linear_x[s0])
        ), 2)
        print output % ('CALC', 'linear_iv linear result: %.2f' % linear_iv)

        linear_results = []
        for degree in range(1, 4):
            z = np.polyfit(linear_x, linear_y, degree)
            f = np.poly1d(z)

            result = round(f(close), 2)

            print output % ('CALC', 'degree: %d, linear IV: %.2f' % (degree, result))
            print output % (
                'COND', 'iv0 > result_iv0 > iv1, %.2f > %.2f > %.2f, %s' % (
                    linear_y[s0], result, linear_y[s1], linear_y[s0] > result > linear_y[s1]
                )
            )
            print output % (
                'COND', 'linear_iv <= linear_iv0, %.2f <= %.2f, %s' % (
                    result, linear_iv, result <= linear_iv
                )
            )

            if linear_y[s0] > result > linear_y[s1] and result <= linear_iv:
                linear_results.append(result)

        if len(linear_results):
            mean_linear_iv = round(np.mean(linear_results), 2)
            print output % ('CALC', 'linear_iv poly result: %.2f' % mean_linear_iv)
        else:
            mean_linear_iv = linear_iv
            print output % ('FILL', 'poly results no mean, fill: %.2f' % mean_linear_iv)

        print '-' * 70
        print output % ('SEC', 'calculate poly iv using poly1d')
        print '-' * 70

        poly1d_x = sorted(results.keys())
        poly1d_y = np.array([np.mean([i['poly1d'] for i in results[k]]) for k in linear_x])
        s0 = self.nearby(poly1d_x, close)
        s1 = self.nearby(poly1d_x, close, True)
        s0, s1 = sorted([s0, s1])
        for strike, impl_vol in zip(poly1d_x, poly1d_y):
            print output % ('DATA', 'strike: %.2f, impl_vol: %.2f' % (strike, impl_vol))

        print output % ('NEAR', '%.2f(%.2f), %.2f(%.2f)' % (
            poly1d_x[s0], poly1d_y[s0], poly1d_x[s1], poly1d_y[s1]
        ))
        poly1d_iv = round(poly1d_y[s0] + (
            (poly1d_y[s1] - poly1d_y[s0]) / float(poly1d_x[s1] - poly1d_x[s0]) *
            (close - poly1d_x[s0])
        ), 2)
        print output % ('CALC', 'poly1d_iv linear result: %.2f' % poly1d_iv)

        poly1d_results = []
        for degree in range(1, 4):
            z = np.polyfit(poly1d_x, poly1d_y, degree)
            f = np.poly1d(z)

            result = round(f(close), 2)

            print output % ('CALC', 'degree: %d, poly1d IV: %.2f' % (degree, result))
            print output % (
                'COND', 'iv0 > result_iv0 > iv1, %.2f > %.2f > %.2f, %s' % (
                    poly1d_y[s0], result, poly1d_y[s1], poly1d_y[s0] > result > poly1d_y[s1]
                )
            )
            print output % (
                'COND', 'result_iv0 <= linear_iv0, %.2f <= %.2f, %s' % (
                    result, poly1d_iv, result <= poly1d_iv
                )
            )

            if poly1d_y[s0] > result > poly1d_y[s1] and result <= poly1d_iv:
                poly1d_results.append(result)

        if len(poly1d_results):
            mean_poly1d_iv = round(np.mean(poly1d_results), 2)
            print output % ('CALC', 'poly1d_iv poly result: %.2f' % mean_poly1d_iv)
        else:
            mean_poly1d_iv = poly1d_iv
            print output % ('FILL', 'poly results no mean, fill: %.2f' % mean_poly1d_iv)

        if plot:
            x = poly1d_x
            x.append(close)
            y = list(poly1d_y)
            y.append(poly1d_iv)
            print zip(x, y)

            z = np.polyfit(x, y, 2)
            f = np.poly1d(z)
            x_new = np.linspace(x[0], y[-1], 50)
            y_new = f(x_new)

            plt.plot(x, y, 'o', x_new, y_new)
            plt.xlim([x[0] - 1, x[-1] + 1])
            plt.show()

        return mean_poly1d_iv, mean_linear_iv

    def calc_iv(self, date):
        """

        :param date: pd.datetime
        :return: float
        """
        poly1d_iv0, linear_iv0 = self.calc_cycles(date=date)
        poly1d_iv1, linear_iv1 = self.calc_strikes(date=date)

        close = self.df_stock.ix[date]['close']
        df_date = self.df_all.query(
            'date == %r & name == "CALL"' % date
        ).sort_values('dte')

        dtes = np.sort(df_date['dte'].unique())
        d0, d1 = self.two_nearby(dtes, 365)
        df_date = df_date.query('dte == %d or dte == %d' % (
            dtes[d0], dtes[d1]
        ))
        strikes = np.sort(df_date[df_date.duplicated('strike')]['strike'].unique())
        s0, s1 = self.two_nearby(strikes, close)

        print output % ('SEED', 'dte0: %d, dte1: %d' % (dtes[d0], dtes[d1]))
        print output % ('SEED', 'strike0: %.2f, strike1: %.2f' % (strikes[s0], strikes[s1]))

        query_str = 'dte == %d & strike == %r'
        impl_vol0a = df_date.query(query_str % (dtes[d0], strikes[s0]))['impl_vol'].iloc[0]
        impl_vol0b = df_date.query(query_str % (dtes[d0], strikes[s1]))['impl_vol'].iloc[0]
        impl_vol1a = df_date.query(query_str % (dtes[d1], strikes[s0]))['impl_vol'].iloc[0]
        impl_vol1b = df_date.query(query_str % (dtes[d1], strikes[s1]))['impl_vol'].iloc[0]

        print output % ('DATA', 'dte0: %d, strike0: %.2f, impl_vol: %.2f' % (
            dtes[d0], strikes[s0], impl_vol0a
        ))
        print output % ('DATA', 'dte0: %d, strike1: %.2f, impl_vol: %.2f' % (
            dtes[d0], strikes[s1], impl_vol0b
        ))
        print output % ('DATA', 'dte1: %d, strike0: %.2f, impl_vol: %.2f' % (
            dtes[d1], strikes[s0], impl_vol1a
        ))
        print output % ('DATA', 'dte1: %d, strike1: %.2f, impl_vol: %.2f' % (
            dtes[d1], strikes[s1], impl_vol1b
        ))

        print '-' * 70

        iv_desc = ['poly1d_iv0', 'poly1d_iv1']
        iv_list = [poly1d_iv0, poly1d_iv1]

        results = []
        for desc, iv in zip(iv_desc, iv_list):
            print output % ('DATA', '%s: %.2f' % (desc, iv))
            print output % ('COND', 'iv > impl_vol0a > impl_vol0b, %.2f > %.2f > %.2f, %s' % (
                iv, impl_vol0a, impl_vol0b, iv > impl_vol0a > impl_vol0b
            ))
            print output % ('COND', 'iv < impl_vol1b < impl_vol1a, %.2f < %.2f < %.2f, %s' % (
                iv, impl_vol1b, impl_vol1a, iv < impl_vol1b < impl_vol1a
            ))

            if impl_vol0b < impl_vol0a < iv < impl_vol1b < impl_vol1a:
                results.append(iv)

        impl_vol = round(np.mean(results), 2)
        print output % ('CALC', 'final impl_vol: %.2f for %.2f in 365-days' % (impl_vol, close))

    def calc(self):
        """

        :return:
        """
        for index, data in self.df_stock.iterrows():
            action = ''

            close = data['close']
            # todo: make sure close price is correct for split data

            df_date = self.df_all.query('date == %r & name == "CALL"' % index)

            # if have not 100 right, remove duplicate split data
            df_date = self.remove_split(df_date)
            """:type: pd.DataFrame"""

            print output % ('LOOP', 'date: %s, close: %.2f' % (index.strftime('%Y-%m-%d'), close))

            if len(df_date) == 0:
                print output % ('ERROR', 'date have no options: %s' % index.strftime('%Y-%m-%d'))
                continue

            dtes = np.sort(np.array(df_date['dte'].unique()))
            d0, d1 = self.two_nearby(dtes, 365)
            df_near = df_date.query('dte == %r | dte == %r' % (dtes[d0], dtes[d1]))
            strikes = np.sort(df_near[df_near.duplicated('strike')]['strike'])
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

            if action == 'nearby_dte':
                print output % ('EXIST', 'nearby 365-days in dtes: %d %d' % (dtes[d0], dtes[d1]))
                #self.nearby_365days(close, dtes[d0], df_date)
            elif action == 'single_dte':
                print output % ('WARN', 'single nearby DTE cycle found: %d' % dtes[d0])
            elif action in ('no_dup_strike', 'single_strike'):
                if action == 'single_strike':
                    print output % ('WARN', 'single nearby STRIKE found: %.2f' % strike)
                else:
                    print output % ('WARN', 'no dup STRIKE found both cycles')
            elif action == 'nearby_strike':
                print output % ('EXIST', 'nearby %.2f price found in strike: %.2f' % (close, strike))
            else:
                print output % ('NORM', '2-nearby-cycles, 2-nearby-strikes found')
                print output % ('NORM', 'using normal 3d calculation')

            print '-' * 70

            # break


    # todo: what if split happen? use which close, new or close?
    #
















