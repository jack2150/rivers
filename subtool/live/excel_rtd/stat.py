import os

import numpy as np
import pandas as pd

from base.ufunc import ts
from rivers.settings import QUOTE_DIR


class OpenToCloseEst(object):
    def __init__(self, group, parts):
        self.group = group
        self.parts = parts


class ExcelRtdStatData(object):
    def __init__(self, symbols):
        """
        :param symbols: list
        """
        self.symbols = symbols

        self.df_all = {}

    def get_data(self):
        self.df_all = {}
        for symbol in self.symbols:
            path = os.path.join(QUOTE_DIR, '%s.h5' % symbol)
            db = pd.HDFStore(path)
            try:
                self.df_all[symbol] = db.select('/stock/google')
            except KeyError:
                try:
                    self.df_all[symbol] = db.select('/stock/yahoo')
                except KeyError:
                    raise LookupError('No google/yahoo data: %s' % symbol)

            db.close()

            #
            # self.df_all[symbol] = self.df_all[symbol].sort_index(ascending=False)

    @staticmethod
    def latest_close(df):
        """
        Get latest close price
        :param df: pd.DataFrame
        :return: float
        """
        return df['close'].iloc[-1]

    @staticmethod
    def mean_vol(df):
        """
        Calc average volume for certain days
        :param df: pd.DataFrame
        :return: int, int
        """
        return df.tail(5)['volume'].mean(), df.tail(20)['volume'].mean()

    @staticmethod
    def open_to_close_move(df):
        """
        Generate stat data for estimate open to close move
        from yesterday close to today open
        and for today open to today close
        :param df: pd.DataFrame
        :return: dict
        """
        df_temp = df.copy()
        df_temp['close_open'] = 1 - df['close'].shift(1) / df['open']
        df_temp['open_close'] = 1 - df['open'] / df['close']
        df_temp['oc_diff'] = df_temp['open_close'] - df_temp['close_open']
        # print pd.cut(df_temp['close_open'], 10)
        df_temp['close_open'] = df_temp['close_open'].replace(-np.inf, 0)
        df_temp['open_close'] = df_temp['open_close'].replace(-np.inf, 0)
        df_temp['close_open'] = df_temp['close_open'].replace(np.inf, 0)
        df_temp['open_close'] = df_temp['open_close'].replace(np.inf, 0)

        df_temp['q-cut'] = pd.qcut(df_temp['close_open'], 5)
        df_temp = df_temp.dropna()
        group = df_temp.groupby('q-cut')

        oc_stat = []
        for g in group:
            oc_stat.append({
                'close_open': [float(n) for n in g[0][1:-1].split(', ')],
                'open_close': sorted([
                    [float(n) for n in b[1:-1].split(', ')]
                    for b in pd.qcut(g[1]['oc_diff'], 5).unique()
                ], key=lambda x: x[1])
            })

        return oc_stat

    @staticmethod
    def close_to_open_move(df):
        """
        Close to open, let you make decision to hold overnight or not
        :param df: pd.DataFrame
        :return: list of OpenToCloseEst
        """
        df1 = df.copy()

        df1['c2o$'] = df1['open'] - df1['close'].shift(1)  # after market
        df1['c2o%'] = df1['c2o$'] / df1['close'].shift(1)  # after market
        df1['o2c$'] = df1['close'] - df1['open']
        df1['o2c%'] = df1['o2c$'] / df1['open']

        df1['q-cut'] = pd.qcut(df1['c2o%'], 5)
        df1 = df1.dropna()
        group = df1.groupby('q-cut')

        stats = []
        for g in group:
            # [float(n) for n in g[0][1:-1].split(', ')]
            c2o_group = [float(n) for n in g[0][1:-1].split(', ')]

            o2c_parts = []
            for b in pd.qcut(g[1]['o2c%'], 5).unique():
                o2c_parts.append([float(n) for n in b[1:-1].split(', ')])

            o2c_parts = sorted(o2c_parts)

            stats.append(OpenToCloseEst(c2o_group, o2c_parts))

        return stats

    @staticmethod
    def hl_wide(df):
        """
        Everyday high-low width range for estimate today range
        :param df: pd.DataFrame
        :return: float, float
        """
        width = (df['high'] - df['low']) / df['open']

        return width.tail(5).mean(), width.tail(20).mean()

    @staticmethod
    def std_close(df):
        """
        Generate std data for everyday return for estimate
        today probability pct_change within std or out of std
        :param df: pd.DataFrame
        :return: dict
        """
        df_temp = df.copy()
        df_temp['close_chg'] = df_temp['close'] - df_temp['close'].shift(1)
        df_temp['pct_chg'] = df_temp['close'].pct_change()

        df_last = df_temp[-60:]
        std = round(df_last['pct_chg'].std(), 4)
        df_last['above_std'] = df_last['pct_chg'] >= std
        df_last['below_std'] = df_last['pct_chg'] <= -std
        df_last['out_std'] = (df_last['above_std']) | (df_last['below_std'])

        # calc consec
        out_std = np.array(df_last['out_std'])
        consec = []
        cont = 0
        for i in out_std:
            if i == 0:
                cont += 1
            else:
                if cont > 0:
                    consec += [cont] * cont
                cont = 0
                consec += [0]
        else:
            consec += [cont] * cont

        df_last['consec'] = consec
        values = df_last['consec'].value_counts()
        df_consec = pd.DataFrame(values)
        df_consec['length'] = values / values.index
        df_consec.loc[0, 'length'] = df_consec.ix[0]['consec']
        df_consec = df_consec.reset_index()
        del df_consec['consec']
        df_consec = df_consec.round({'length': 0, 'index': 0})

        # make history price table
        df_last = df_last.round({'close_chg': 2, 'pct_chg': 4}).sort_index(ascending=False)
        history = df_last[[
            'close', 'volume', 'close_chg', 'pct_chg',
            'above_std', 'below_std', 'out_std', 'consec'
        ]].reset_index()

        hp_table = [dict(d) for _, d in history.iterrows()]
        # print history

        # make df_consec table
        cs_table = sorted(
            [[d['index'], d['length']] for _, d in df_consec.iterrows()]
        )

        return {
            'std': {
                'std_value': std,
                'out_std': len(df_last[df_last['out_std']]),
                'in_std': len(df_last[~df_last['out_std']]),
                'above_std': len(df_last[df_last['above_std']]),
                'below_std': len(df_last[df_last['below_std']]),
                'close_gain': len(df_last[df_last['pct_chg'] > 0]),
                'close_loss': len(df_last[df_last['pct_chg'] < 0]),
                '60_day_move': (df_last.iloc[-1]['close'] / df_last.iloc[0]['close']) - 1
            },
            'consec': cs_table,
            'history': hp_table
        }

    class StatData(object):
        def __init__(self, data):
            self.close = data['close']
            self.mean_vol5 = data['mean_vol5']
            self.mean_vol20 = data['mean_vol20']
            self.mean_hl5 = data['mean_hl5']
            self.mean_hl20 = data['mean_hl20']
            self.oc_stat = data['oc_stat']
            self.co_stat = data['co_stat']
            self.std_close = data['std_close']

    def get_symbol_stat(self, symbol):
        """
        Get symbol day statistics
        :param symbol: str
        :return: StatData
        """
        df = self.df_all[symbol]
        close = self.latest_close(df)
        vol5, vol20 = self.mean_vol(df)
        hl5, hl20 = self.hl_wide(df)
        oc_stat = self.open_to_close_move(df)
        co_stat = self.close_to_open_move(df)
        std_close = self.std_close(df)

        return self.StatData({
            'close': close,
            'mean_vol5': vol5,
            'mean_vol20': vol20,
            'mean_hl5': hl5,
            'mean_hl20': hl20,
            'oc_stat': oc_stat,
            'co_stat': co_stat,
            'std_close': std_close,
        })
