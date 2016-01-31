"""
Type: Technical Analysis
Name: Momentum rule
Method: Change of momentum
"""

import numpy as np


def handle_data(df, span=0):
    df['close0'] = df['close'].shift(span)
    df['net_chg'] = df['close'] - df['close0']
    f = lambda x: 'BUY' if x > 0 else ('SELL' if x < 0 else np.nan)
    df['signal'] = df['net_chg'].apply(f)
    return df.copy()


def create_signal(df, holding=0):
    df1 = df.copy()
    df1['date1'] = df1['date'].shift(-holding)
    df1['close1'] = df1['close'].shift(-holding)

    df2 = df1[df1['signal'] != df1['signal'].shift(1)].dropna()[1:]  # always skip first

    df2['date0'] = df2['date']

    df2['close0'] = df2['close']
    df2['signal1'] = df2['signal'].apply(lambda x: 'SELL' if x == 'BUY' else 'BUY')

    df2 = df2.reindex_axis(
        ['date0', 'date1', 'signal', 'signal1', 'close0', 'close1'], axis=1
    ).dropna()
    df2.columns = ['date0', 'date1', 'signal0', 'signal1', 'close0', 'close1']

    df2['holding'] = df2['date1'] - df2['date0']
    df2['pct_chg'] = (df2['close1'] - df2['close0']) / df2['close0']

    # apply algorithm result
    f = lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg']
    df2['pct_chg'] = df2.apply(f, axis=1)
    df2['pct_chg'] = df2['pct_chg']

    # only up
    df2 = df2[df2['signal0'] == 'SELL']

    return df2.copy()



