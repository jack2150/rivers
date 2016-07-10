import numpy as np


def create_order(df_signal, side=('follow', 'reverse', 'buy', 'sell')):
    """
    Trade stock with stop loss order
    :param df_signal: DataFrame
    :param side: str
    :return: DataFrame
    """
    df = df_signal.copy()

    if side == 'buy':
        df['signal0'] = 'BUY'
        df['signal1'] = 'SELL'
    elif side == 'sell':
        df['signal0'] = 'SELL'
        df['signal1'] = 'BUY'
    elif side == 'reverse':
        temp = df['signal0'].copy()
        df['signal0'] = df['signal1']
        df['signal1'] = temp

    df['bp_effect'] = df['close0']
    df['close0'] = df.apply(
        lambda x: x['close0'] if x['signal0'] == 'BUY' else -x['close0'],
        axis=1
    )
    df['close1'] = df.apply(
        lambda x: x['close1'] if x['signal1'] == 'BUY' else -x['close1'],
        axis=1
    )
    df['holding'] = df['date1'] - df['date0']
    df['pct_chg'] = (-df['close1'] - df['close0']) / df['close0']
    df['pct_chg'] = df.apply(
        lambda x: x['pct_chg'] if x['signal0'] == 'BUY' else x['pct_chg'] * -1,
        axis=1
    )

    # for stock option quantity multiply
    df['sqm0'] = df.apply(lambda x: -1 if x['signal0'] == 'SELL' else 1, axis=1)
    df['sqm1'] = -df['sqm0']
    df['oqm0'] = 0
    df['oqm1'] = 0

    df = df.round({
        'pct_chg': 4,
    })

    return df


def join_data(df_order, df_stock):
    """
    Join df_trade data into daily trade data
    :param df_order: pd.DataFrame
    :param df_stock: pd.DataFrame
    :return: list
    """
    df_list = []
    df_stock0 = df_stock.set_index('date')
    for index, data in df_order.iterrows():
        df_date = df_stock0[data['date0']:data['date1']].copy()
        df_date['pct_chg'] = df_date['close'].pct_change()
        df_date['pct_chg'] = df_date['pct_chg'].fillna(value=0)
        df_date['pct_chg'] = df_date['pct_chg'].apply(
            lambda x: 0 if x == np.inf else x
        )

        if data['signal0'] == 'SELL':
            df_date['pct_chg'] = -df_date['pct_chg'] + 0

        df_date.reset_index(inplace=True)
        df_date = df_date[['date', 'close', 'pct_chg']]
        df_date.columns = ['date', 'stock', 'pct_chg']

        df_list.append(df_date)

    return df_list

