"""
Type: Technical Analysis
Name: Momentum rule
Method: Change of momentum
"""
from pandas import rolling_mean
import numpy as np


def handle_data(df, span=0):
    df['sma'] = rolling_mean(df['close'], span)
    df['p-sma'] = df['close'] - df['sma']
    f = lambda x: 'BUY' if x > 0 else ('SELL' if x < 0 else np.nan)
    df['signal'] = df['p-sma'].apply(f)
    return df.copy()


def create_signal(df):
    df2 = df[df['signal'] != df['signal'].shift(1)].dropna()
    # df2 = df2.append(df.tail(1))  # last date
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
    f = lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg']
    df2['pct_chg'] = df2.apply(f, axis=1)
    df2['pct_chg'] = df2['pct_chg']

    return df2.copy()


