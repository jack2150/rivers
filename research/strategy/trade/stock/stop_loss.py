import numpy as np


def create_order(df_signal, df_stock, side=('follow', 'reverse', 'buy', 'sell'), percent=0):
    """
    Trade stock with stop loss order
    :param df_signal: DataFrame
    :param df_stock: DataFrame
    :param side: str
    :param percent: int or float
    :return: DataFrame
    """
    df0 = df_stock.copy()
    df_signal1 = df_signal.copy()

    if side == 'buy':
        df_signal1['signal0'] = 'BUY'
        df_signal1['signal1'] = 'SELL'
    elif side == 'sell':
        df_signal1['signal0'] = 'SELL'
        df_signal1['signal1'] = 'BUY'
    elif side == 'reverse':
        temp = df_signal1['signal0'].copy()
        df_signal1['signal0'] = df_signal1['signal1']
        df_signal1['signal1'] = temp

    loss_pct = percent / 100.0
    loss_hits = list()
    exit_dates = list()
    exit_times = list()
    exit_prices = list()

    for index, signal in df_signal1.iterrows():
        df_temp = df0.ix[signal['date0']:signal['date1']][1:]

        if signal['signal0'] == 'BUY':
            stop_limit = np.round(signal['close0'] * (1 - loss_pct), 2)

            df_temp['sold'] = df_temp.apply(
                lambda x: any(
                    [True if x[n] <= stop_limit else False for n in ('open', 'high', 'low', 'close')]),
                axis=1
            )
            try:
                exit_date = df_temp[df_temp['sold']].index.values[0]
                exit_time = 'during'

                # check use what
                exit_price = stop_limit
                if df_temp.ix[exit_date]['open'] <= stop_limit:
                    exit_time = 'open'
                    exit_price = df_temp.ix[exit_date]['open']
                loss_hit = True
            except IndexError:
                # no stop loss hit
                exit_date = df_temp.index.values[-1]
                exit_time = 'close'
                exit_price = df_temp.ix[exit_date]['close']
                loss_hit = False
        else:
            stop_limit = signal['close0'] * (1 + loss_pct)
            df_temp['sold'] = df_temp.apply(
                lambda x: any(
                    [True if x[n] >= stop_limit else False for n in ('open', 'high', 'low', 'close')]),
                axis=1
            )
            try:
                exit_date = df_temp[df_temp['sold']].index.values[0]

                # check use what
                exit_time = 'during'
                exit_price = stop_limit
                if df_temp.ix[exit_date]['open'] >= stop_limit:
                    exit_price = df_temp.ix[exit_date]['open']
                    exit_time = 'open'
                loss_hit = True
            except IndexError:
                # no stop loss hit
                exit_date = df_temp.index.values[-1]
                exit_time = 'close'
                exit_price = df_temp.ix[exit_date]['close']
                loss_hit = False

        loss_hits.append(loss_hit)
        exit_dates.append(exit_date)
        exit_times.append(exit_time)
        exit_prices.append(exit_price)

    df1 = df_signal1.copy()

    df1['date1'] = exit_dates
    df1['exit'] = exit_times
    df1['close1'] = np.round(exit_prices, 2)

    df1['holding'] = df1['date1'] - df1['date0']

    df1['pct_chg'] = (df1['close1'] - df1['close0']) / df1['close0']
    df1['pct_chg'] = np.round(df1.apply(
        lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg'],
        axis=1
    ), 4)

    # for stock option quantity multiply
    df1['sqm0'] = df1.apply(lambda x: -1 if x['signal0'] == 'SELL' else 1, axis=1)
    df1['sqm1'] = -df1['sqm0']
    df1['oqm0'] = 0
    df1['oqm1'] = 0

    return df1
