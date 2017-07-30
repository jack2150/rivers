import numpy as np
import pandas as pd
from base.ufunc import ts


class ReportStatPrice(object):
    def __init__(self, df_stock, date0='', date1=''):
        self.df_stock = df_stock.copy()
        """:type: pd.DataFrame"""

        if date0 != '':
            self.df_stock = self.df_stock[date0:]

        if date1 != '':
            self.df_stock = self.df_stock[:date1]

        self.date0 = self.df_stock.index[0].strftime('%Y-%m-%d')
        self.date1 = self.df_stock.index[-1].strftime('%Y-%m-%d')
        # print self.date0, self.date1

    @staticmethod
    def calc_bins(days):
        """

        :param days:
        :return:
        """
        if days < 10:
            bins = np.arange(-20, 21, 1)
            bins = [-100, -50, ] + list(bins) + [50, 100]
        elif days < 30:
            bins = np.arange(-40, 42, 2)
            bins = [-100, -60, ] + list(bins) + [60, 100]
        else:
            bins = np.arange(-60, 63, 3)
            bins = [-100, -80, ] + list(bins) + [80, 100]

        return bins

    def main_stat(self):
        """
        bull vs bear, std, count,
        :return:
        """
        df_stock = self.df_stock.copy()
        """:type: pd.DataFrame"""

        df_stock['pct_chg'] = df_stock['close'].pct_change() * 100
        count = len(df_stock)
        std = round(df_stock['pct_chg'].std(), 2)

        # ts(df_stock.tail())
        move_up = len(df_stock[df_stock['pct_chg'] > 0])
        move_down = len(df_stock[df_stock['pct_chg'] < 0])
        below_std = len(df_stock[df_stock['pct_chg'] > std])
        above_std = len(df_stock[df_stock['pct_chg'] < -std])
        stat_data = {
            'up': '%d (%.2f%%)' % (move_up, move_up / float(count) * 100),
            'down': '%d (%.2f%%)' % (move_down, move_down / float(count) * 100),
            'mean': round(df_stock['pct_chg'].mean(), 2),
            'median': round(df_stock['pct_chg'].median(), 2),
            'min': round(df_stock['pct_chg'].min(), 2),
            'max': round(df_stock['pct_chg'].max(), 2),
            'std': std,
            'below_std': below_std,
            'above_std': above_std,
            'within_std': len(df_stock) - below_std - above_std,
        }

        # ts(pd.DataFrame(stat_data, index=[0]))
        return stat_data

    def move_dist(self, blank=True):
        """
        Move % change distribution
        :type blank: bool
        :return: pd.DataFrame
        """
        df_stock = self.df_stock.copy()
        """:type: pd.DataFrame"""

        df_stock['pct_chg'] = df_stock['close'].pct_change() * 100
        bins = self.calc_bins(1)
        # print bins

        df_stock['cut'] = pd.cut(df_stock['pct_chg'], bins=bins)

        grouped = df_stock.groupby('cut')
        df_group = pd.DataFrame(grouped['close'].count())

        if blank:
            df_group = df_group[df_group['close'] > 0]

        df_group['left'] = [x.left for x in df_group.index]
        df_group['right'] = [x.right for x in df_group.index]

        df_group['chance'] = df_group['close'] / float(df_group['close'].sum()) * 100

        # % of below or above dist
        total0 = 0
        total1 = 0
        l0 = []
        l1 = []
        for left, close0, close1 in zip(df_group['left'], df_group['close'], df_group['close'].iloc[::-1]):
            total0 += close0
            total1 += close1

            l0.append(total0)
            l1.append(total1)

        l1 = [l for l in reversed(l1)]
        df_group['cumsum0'] = l0
        df_group['cumsum1'] = l1
        df_group['roll-sum'] = df_group.apply(
            lambda t: t['cumsum1'] if t['left'] > -1 else t['cumsum0'],
            axis=1
        )
        df_group['prob-in'] = df_group['roll-sum'] / float(df_group['close'].sum()) * 100
        df_group['prob-ex'] = 100 - df_group['prob-in']

        # print [str(t) for t in s.index]
        # print grouped['pct_chg-60'].mean()
        # format
        if blank:
            columns = ['close', 'chance', 'roll-sum', 'prob-in', 'prob-ex', 'cumsum0']
        else:
            columns = ['close', 'chance', 'roll-sum', 'prob-in', 'prob-ex', 'right']

        df_group = df_group[columns]
        df_group = df_group.round({'prob-in': 2, 'prob-ex': 2, 'chance': 2})

        # ts(df_group)

        return df_group

    def make_bdays(self, days):
        """

        :param days:
        :return:
        """
        df_stock = self.df_stock.copy()
        """:type: pd.DataFrame"""
        df_stock['pct_chg'] = df_stock['close'].pct_change() * 100
        name = 'pc_day'
        df_stock[name] = df_stock['close'].pct_change(-days) * 100

        # bins need update for longer period
        bins = self.calc_bins(1)

        # print bins
        df_stock['cut'] = pd.cut(df_stock['pct_chg'], bins=bins)
        return df_stock, name

    def bday_dist(self, days):
        """
        Move % change, enter hold bdays return
        :param days: int
        :return: pd.DataFrame
        """
        df_stock, name = self.make_bdays(days)

        grouped = df_stock.groupby('cut')
        df_group = pd.DataFrame(grouped['close'].count())
        df_group['d_mean'] = grouped[name].mean()
        df_group['d_median'] = grouped[name].median()
        df_group['d_std'] = grouped[name].std()

        df_group['d_bull'] = grouped[name].apply(
            lambda x: len([y for y in x if y > 0]) / float(len(x) if len(x) else 1) * 100
        )
        df_group['d_bear'] = grouped[name].apply(
            lambda x: len([y for y in x if y < 0]) / float(len(x) if len(x) else 1) * 100
        )

        df_group = df_group[df_group['close'] > 0]

        # ts(df_group)
        df_group = df_group.round(2)
        df_group = df_group.fillna(0)

        return df_group

    def stem(self, percent, days):
        """
        based on stat theory,
        bdays % move to % move (sample)
        :return:
        """
        # print '(%d, %d]' % (percent - 1, percent)
        bins = self.calc_bins(days)

        df_stock, name = self.make_bdays(days)
        df_stock['cut2'] = pd.cut(df_stock['pc_day'], bins=bins)
        df_stock['left'] = df_stock['cut'].apply(lambda x: x.left)
        df_stock['right'] = df_stock['cut'].apply(lambda x: x.right)
        # ts(df_stock)

        df_pct = df_stock[df_stock['right'] == percent]
        # ts(df_pct)

        grouped = df_pct.groupby('cut2')
        df_group = pd.DataFrame(grouped['close'].count())
        total = df_group['close'].sum()
        df_group['chance'] = df_group['close'] / float(total) * 100.0
        df_group['left'] = [x.left for x in df_group.index]
        df_group['right'] = [x.right for x in df_group.index]

        # % of below or above dist
        total0 = 0
        total1 = 0
        l0 = []
        l1 = []
        for left, close0, close1 in zip(df_group['left'], df_group['close'], df_group['close'].iloc[::-1]):
            total0 += close0
            total1 += close1

            l0.append(total0)
            l1.append(total1)

        l1 = [l for l in reversed(l1)]
        df_group['t0'] = l0
        df_group['t1'] = l1
        df_group['roll-sum'] = df_group.apply(
            lambda t: t['t1'] if t['left'] > -1 else t['t0'],
            axis=1
        )
        df_group['op_in'] = df_group['roll-sum'] / float(df_group['close'].sum()) * 100
        df_group['op_out'] = 100 - df_group['op_in']

        # extra
        df_group['sum'] = grouped['pc_day'].sum()
        df_group['mean'] = grouped['pc_day'].mean()
        df_group['std'] = grouped['pc_day'].std()
        df_group = df_group.fillna(0)

        # ts(df_group)

        # format
        df_group = df_group[df_group['close'] > 0]
        df_group = df_group.round({
            'chance': 1, 'op_in': 1, 'op_out': 1, 'sum': 1, 'mean': 1, 'std': 1
        })
        df_group = df_group[[
            'close', 'chance', 'roll-sum', 'op_in', 'op_out', 'sum', 'mean', 'std'
        ]]

        # ts(df_group)

        return df_group


# todo: large volume vs small volume, only need to change the input df_stock
# todo: 3 parts, cut, after move, consec... quantile?
# todo: improve fundamental on statistics
