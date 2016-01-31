"""
Type: Event Earning
Name: Earning Movement
Method: Enter before and exit after
"""
import itertools
import numpy as np
import pandas as pd
from rivers.settings import QUOTE


def handle_data(df, move=('up', 'down'), percent=0, bdays=0):
    symbol = df.ix[df.index.values[0]]['symbol']

    db = pd.HDFStore(QUOTE)
    df_earning = db.select('event/earning/%s' % symbol.lower())
    """:type: DataFrame"""
    db.close()
    df_earning = df_earning.set_index('actual_date').sort_index(ascending=True)

    # verify earnings
    s = [int(q[1:]) for q in df_earning['quarter']]
    r = list(itertools.chain.from_iterable([range(1, 5) * int(np.ceil(len(df_earning) / 4.0) + 1)]))
    if s != r[s[0] - 1:s[0] - 1 + len(s)]:
        print s
        print r[s[0] - 1:s[0] - 1 + len(s)]
        raise LookupError('%s earning is missing quarter, need valid data' % symbol)

    dates = list(df['date'])

    release_dates = list()
    for index, earning in df_earning.iterrows():
        day = 1 if earning['release'] == 'After Market' else 0

        try:
            release_dates.append(dates[dates.index(index) + day])
        except ValueError:
            pass  # no earnings date found, no data or date not found

    df0 = df.copy()
    df0['earning'] = df0['date'].apply(lambda x: x in release_dates)
    df0['pct_chg0'] = df0['close'].pct_change()

    if move == 'up':
        df0['found0'] = df0['pct_chg0'] > percent / 100.0
    elif move == 'down':
        df0['found0'] = df0['pct_chg0'] < percent / 100.0 * -1

    df0['found'] = df0['earning'] & df0['found0']
    df0['date1'] = df0['date'].shift(-bdays)
    df0['close1'] = df0['close'].shift(-bdays)

    del df0['pct_chg0']
    del df0['found0']

    return df0


def create_signal(df, side=('buy', 'sell')):
    df1 = df[df['found']]

    df1['signal0'] = side.upper()
    df1['signal1'] = 'SELL' if side.upper() == 'BUY' else 'BUY'

    df1 = df1.reindex_axis(
        ['date', 'date1', 'signal0', 'signal1', 'close', 'close1'], axis=1
    ).dropna()

    df1.columns = ['date0', 'date1', 'signal0', 'signal1', 'close0', 'close1']

    df1['holding'] = df1['date1'] - df1['date0']
    df1['pct_chg'] = (df1['close1'] - df1['close0']) / df1['close0']

    # apply algorithm result
    f = lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg']

    if len(df1) > 0:
        df1['pct_chg'] = df1.apply(f, axis=1)
        df1['pct_chg'] = df1['pct_chg']
    else:
        raise ValueError('Arguments not found, please reset input value.')

    return df1.copy()
