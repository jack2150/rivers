"""
Type: High low movement and close result
Name: Day percent move
Method: Buy after a swing day that move down % and move up % then close higher or lower
"""


def handle_data(df, pct_up=0, pct_down=0, close=('higher', 'lower'), bdays=0):
    df0 = df.copy()

    pct_up = -pct_up if pct_up < 0 else pct_up
    pct_down = -pct_down if pct_down > 0 else pct_down

    df0['open_to_high'] = (df0['high'] - df0['open']) / df0['open']
    df0['found0'] = df0['open_to_high'] >= pct_up / 100.0

    df0['open_to_low'] = (df0['low'] - df0['open']) / df0['open']
    df0['found1'] = df0['open_to_low'] <= pct_down / 100.0

    df0['open_to_close'] = (df0['close'] - df0['open']) / df0['open']
    if close == 'higher':
        df0['found2'] = df0['open_to_close'] > 0
    elif close == 'lower':
        df0['found2'] = df0['open_to_close'] < 0

    df0['found_all'] = df0.apply(lambda x: x['found0'] and x['found1'] and x['found2'], axis=1)

    df0['date1'] = df0['date'].shift(-bdays)
    df0['close1'] = df0['close'].shift(-bdays)

    return df0


def create_signal(df, side=('buy', 'sell')):
    df1 = df.copy()

    df1 = df1[df1['found_all']].dropna()

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

