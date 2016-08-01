import logging
import numpy as np
import pandas as pd
from scipy.stats import norm

from base.ufunc import ts
from data.option.day_iv.calc import today_iv, correct_prob
from research.strategy.trade.option_cask import get_price_ask
from research.strategy.trade.option_cs import get_cycle_strike, get_cycle_strike2

logger = logging.getLogger('views')


def reverse(x):
    return 'SELL' if x == 'BUY' else 'BUY'


def create_order(df_signal, df_all,
                 side=('follow', 'reverse', 'buy', 'sell'),
                 cycle=0, pct0=0, pct1=0):
    """
    Single CALL option strategy, support follow, long, short
    :param df_signal: pd.DataFrame
    :param df_all: pd.DataFrame
    :param side: str ('follow', 'long', 'short')
    :param cycle: int (can only be positive)
    :param pct1: int
    :param pct0: int
    :return: pd.DataFrame
    """
    df_signal0 = df_signal.copy()

    if side == 'buy':
        df_signal0['signal0'] = 'BUY'
        df_signal0['signal1'] = 'SELL'
    elif side == 'sell':
        df_signal0['signal0'] = 'SELL'
        df_signal0['signal1'] = 'BUY'
    elif side == 'reverse':
        df_signal0['signal0'] = df_signal0['signal0'].apply(reverse)
        df_signal0['signal1'] = df_signal0['signal1'].apply(reverse)

    signals = []
    for index, data in df_signal0.iterrows():
        try:
            target0 = data['close0'] * (1 + (pct0 / 100.0))
            target1 = data['close0'] * (1 + (pct1 / 100.0))

            """
            option0a, option0b = get_cycle_strike(
                df_all, data['date0'], data['date1'], 'CALL', target0, cycle, 0
            )

            option1a, option1b = get_cycle_strike(
                df_all, data['date0'], data['date1'], 'PUT', target1, cycle, -1
            )
            """
            option0a, option0b, option1a, option1b = get_cycle_strike2(
                df_all, data['date0'], data['date1'],
                'CALL', target0, cycle, 0,
                'PUT', target1, cycle, -1
            )

            # df = pd.DataFrame([option0a, option0b, option1a, option1b])
            # ts(df)

            data['stock0'] = data['close0']
            data['stock1'] = data['close1']
            data['code0'] = option0a['option_code']
            data['code1'] = option1a['option_code']
            data['strike0'] = option0a['strike']
            data['strike1'] = option1a['strike']
            # buy sell are same
            if side == 'buy':
                data['price0a'] = option0a['buy']
                data['price1a'] = -option1a['sell']
                data['price0b'] = -option0b['sell']
                data['price1b'] = option1b['buy']
            else:
                data['price0a'] = -option0a['sell']
                data['price1a'] = option1a['buy']
                data['price0b'] = option0b['buy']
                data['price1b'] = -option1b['sell']

            signals.append(data)
        except (KeyError, ValueError, IndexError):
            logger.info('Not found, date: %s cycle: %s pct0: %s pct1: %s' % (
                data['date0'].strftime('%Y-%m-%d'), cycle, pct0, pct1
            ))

    df = pd.DataFrame(signals)
    df['close0'] = df['price0a'] + df['price1a']
    df['close1'] = df['price0b'] + df['price1b']
    df = df[df['close0'] != 0]

    df['bp_effect'] = df['stock0'] * 100
    df['net_chg'] = -df['close1'] - df['close0']
    df['pct_chg'] = df['net_chg'] / df['stock0']

    df['sqm0'] = 0
    df['sqm1'] = 0
    df['oqm0'] = df.apply(lambda x: -2 if x['signal0'] == 'SELL' else 2, axis=1)
    df['oqm1'] = -df['oqm0']

    df = df.round({
        'pct_chg': 4,
        'net_chg': 2
    })

    return df


def join_data(df_order, df_stock, df_all):
    """
    Use for trade report view to check each trade
    :param df_order: pd.DataFrame
    :param df_stock: pd.DataFrame
    :param df_all: pd.DataFrame
    :return: list
    """
    df_stock0 = df_stock.set_index('date')
    df_list = []
    for index, data in df_order.iterrows():
        df_both = df_all.query(
            '(option_code == %r | option_code == %r) & date >= %r  & date <= %r' % (
                data['code0'], data['code1'], data['date0'], data['date1']
            )
        )[['date', 'option_code', 'dte', 'sell', 'buy', 'strike']]

        df0 = df_both.query('option_code == %r' % data['code0'])
        df1 = df_both.query('option_code == %r' % data['code1'])
        df_join = pd.merge(df0, df1, on='date', suffixes=(0, 1))

        if data['signal0'] == 'BUY':
            first = df_join['buy0'] - df_join['sell1']
            remain = df_join['sell0'] - df_join['buy1']
            df_join['signal'] = ['BUY'] + ['SELL'] * len(remain[1:])
            df_join['option'] = [first.iloc[0]] + list(remain[1:])
        else:
            first = -df_join['sell0'] + df_join['buy1']
            remain = -df_join['buy0'] + df_join['sell1']
            df_join['signal'] = ['SELL'] + ['BUY'] * len(remain[1:])
            df_join['option'] = [first.iloc[0]] + list(remain[1:])

        df_join['pos_net'] = df_join['option'] - df_join['option'].iloc[0]
        df_join['pct_chg'] = df_join['pos_net'] / np.abs(df_join['option'].iloc[0]) + 0

        df_join = df_join.drop([
            'sell0', 'buy0', 'sell1', 'buy1', 'strike0', 'strike1', 'dte1'
        ], axis=1)
        df_close = df_stock0[data['date0']:data['date1']]
        df_close = df_close[['close']].reset_index()
        df_both = pd.merge(df_join, df_close, on='date')
        df_both.rename(index=str, columns={'close': 'stock', 'dte0': 'dte'}, inplace=True)

        # print df.to_string(line_width=1000)
        df_both = df_both.replace([np.inf, -np.inf], np.nan)
        df_both = df_both.fillna(0)

        df_both = df_both.round({
            'pos_net': 2,
            'pct_chg': 2,
        })

        df_list.append(df_both)

    return df_list
