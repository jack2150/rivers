"""
Type: Basic percent move
Name: Day close near high or lower
Method: Buy after a day that close near high or low, and hold N days
"""
import numpy as np


def handle_data(df, peak=('high', 'low'), pct_move=0, pct_range=0, bdays=0):
    df0 = df.copy()

    df0['move'] = (df0[peak] - df0['open']) / df0['open']
    df0['found0'] = np.abs(df0['move']) > (pct_move / 100.0)

    df0['range0'] = df0[peak] * (1 - (pct_range / 100.0))
    df0['range1'] = df0[peak] * (1 + (pct_range / 100.0))

    df0['found1'] = df0.apply(lambda x: x['range0'] <= x['close'] <= x['range1'], axis=1)

    df0['found'] = df0['found0'] & df0['found1']
    df0['date1'] = df0['date'].shift(-bdays)
    df0['close1'] = df0['close'].shift(-bdays)

    return df0


def create_signal(df, side=('buy', 'sell')):
    df1 = df.copy()

    df1 = df1[df1['found']].dropna()

    if side == 'buy':
        df1['signal0'] = 'BUY'
        df1['signal1'] = 'SELL'
    elif side == 'sell':
        df1['signal0'] = 'SELL'
        df1['signal1'] = 'BUY'

    df1 = df1.reindex_axis(
        ['date', 'date1', 'signal0', 'signal1', 'close', 'close1'], axis=1
    ).dropna()

    df1.columns = ['date0', 'date1', 'signal0', 'signal1', 'close0', 'close1']

    df1['holding'] = df1['date1'] - df1['date0']
    df1['pct_chg'] = (df1['close1'] - df1['close0']) / df1['close0']

    # apply algorithm result
    f = lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg']
    df1['pct_chg'] = df1.apply(f, axis=1)
    df1['pct_chg'] = df1['pct_chg']

    return df1.copy()

