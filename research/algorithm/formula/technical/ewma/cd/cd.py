"""
Type: Technical Analysis
Name: Exponential weighted moving average
Method: Change direction
"""

import numpy as np
from pandas.stats.moments import ewma


def handle_data(df, span=0, previous=0):
    df['ema1'] = ewma(df['close'], span=span, min_periods=span)
    df['ema0'] = df['ema1'].shift(previous)
    df['ema_chg'] = df['ema1'] - df['ema0']
    df['signal'] = df['ema_chg'].apply(
        lambda x: 'BUY' if x > 0 else ('SELL' if x < 0 else np.nan)
    )
    return df.copy()


def create_signal(df):
    df2 = df[df['signal'] != df['signal'].shift(1)].dropna()
    df2 = df2[1:]  # skip first

    df2['date0'] = df2['date'].shift(1)
    df2['close0'] = df2['close'].shift(1)
    df2['signal0'] = df2['signal'].shift(1)

    df2 = df2.reindex_axis(
        ['date0', 'date', 'signal0', 'signal', 'close0', 'close'], axis=1
    ).dropna()

    df2.columns = ['date0', 'date1', 'signal0', 'signal1', 'close0', 'close1']

    df2['holding'] = df2['date1'] - df2['date0']
    df2['pct_chg'] = (df2['close1'] - df2['close0']) / df2['close0']

    # apply algorithm result
    df2['pct_chg'] = df2.apply(
        lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg'],
        axis=1
    )
    # df2['pct_chg'] = df2['pct_chg']

    return df2.copy()


