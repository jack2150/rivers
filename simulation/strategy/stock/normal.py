import numpy as np


def create_order(df_stock, df_signal, side=('follow', 'buy', 'sell')):
    """
    Trade stock with stop loss order
    :param df_stock: DataFrame
    :param df_signal: DataFrame
    :return: DataFrame
    """
    df = df_signal.copy()

    if side == 'buy':
        df['signal0'] = 'BUY'
        df['signal1'] = 'SELL'
    elif side == 'sell':
        df['signal0'] = 'SELL'
        df['signal1'] = 'BUY'

    df['holding'] = df['date1'] - df['date0']

    f = lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg']
    df['pct_chg'] = (df['close1'] - df['close0']) / df['close0']
    df['pct_chg'] = np.round(df.apply(f, axis=1), 4)

    # for stock option quantity multiply
    f = lambda x: -1 if x['signal0'] == 'SELL' else 1
    df['sqm0'] = df.apply(f, axis=1)
    df['sqm1'] = df.apply(f, axis=1) * -1
    df['oqm0'] = 0
    df['oqm1'] = 0

    return df