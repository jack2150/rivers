"""
Type: Technical Analysis
Name: Exponential weighted moving average
Method: Change direction, signal after 2 days
"""
import numpy as np
from pandas.stats.moments import ewma


def handle_data(df, span, previous):
    df['ema1'] = ewma(df['close'], span=span, min_periods=span)
    df['ema0'] = df['ema1'].shift(previous)
    df['ema_chg'] = df['ema1'] - df['ema0']
    f = lambda x: 'BUY' if x > 0 else ('SELL' if x < 0 else np.nan)
    df['signal'] = df['ema_chg'].apply(f)
    return df.copy()


# noinspection PyUnresolvedReferences
def create_signal(df, after):
    df1 = df.copy()
    df1['date2'] = df1['date'].shift(-after)
    df1['close2'] = df1['close'].shift(-after)

    df2 = df1[df1['signal'] != df1['signal'].shift(1)].dropna()
    df2 = df2[1:]  # skip first

    df2['date0'] = df2['date'].shift(1)
    df2['close0'] = df2['close'].shift(1)
    df2['signal0'] = df2['signal'].shift(1)

    df2['date2'] = df2['date2'].shift(1)
    df2['close2'] = df2['close2'].shift(1)

    #print df2.to_string(line_width=300)

    df2 = df2.reindex_axis(
        ['date0', 'date2', 'date',
         'signal0', 'signal',
         'close0', 'close2', 'close'], axis=1
    ).dropna()

    df2.columns = [
        'date0', 'date2', 'date1',
        'signal0', 'signal1',
        'close0', 'close2', 'close1'
    ]

    df2['holding'] = df2['date1'] - df2['date0']
    df2['holding'] = df2['holding'].apply(
        lambda x: int(x.astype('timedelta64[D]') / np.timedelta64(1, 'D'))
    )

    # apply only after days
    df2 = df2[df2['holding'] >= after]
    df2.drop(['date0', 'close0'], axis=1, inplace=True)
    df2.columns = ['date0', 'date1', 'signal0', 'signal1',
                   'close0', 'close1', 'holding']

    # calculate pct change
    df2['pct_chg'] = (df2['close1'] - df2['close0']) / df2['close0']

    # apply algorithm result
    f = lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg']
    df2['pct_chg'] = df2.apply(f, axis=1)
    df2['pct_chg'] = df2['pct_chg']

    return df2.copy()


