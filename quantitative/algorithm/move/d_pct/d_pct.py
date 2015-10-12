"""
Type: Basic percent move
Name: Day percent move
Method: Buy after a certain move, and hold N days
"""


def handle_data(df, move=('up', 'down'), pct_from=0, pct_to=0, bdays=0):
    df0 = df.copy()

    p0 = 0
    p1 = 0
    if move == 'up':
        p0 = pct_from / 100.0
        p1 = pct_to / 100.0
        f = lambda x: p0 <= x <= p1
    elif move == 'down':
        p0 = pct_from / -100.0
        p1 = pct_to / -100.0
        f = lambda x: p1 <= x <= p0

    df0['pct_chg'] = df0['close'].pct_change()
    df0['found'] = df0['pct_chg'].apply(f)
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
    if len(df1):
        f = lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg']
        df1['pct_chg'] = df1.apply(f, axis=1)
        df1['pct_chg'] = df1['pct_chg']
    else:
        raise ValueError('No enough data.')

    return df1.copy()

