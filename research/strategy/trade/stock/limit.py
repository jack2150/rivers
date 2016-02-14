import numpy as np


def create_order(df_signal, df_stock, side=('follow', 'reverse', 'buy', 'sell'), percent=0):
    """
    Trade stock with stop loss order
    :param df_signal: DataFrame
    :param df_stock: DataFrame
    :param side: str
    :param percent: float
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

    limit_pct = percent / 100.0
    loss_hits = list()
    exit_dates = list()
    exit_times = list()
    exit_prices = list()

    for index, signal in df_signal1.iterrows():
        df_temp = df0.ix[signal['date0']:signal['date1']][1:]

        if signal['signal0'] == 'BUY':
            limit = np.round(signal['close0'] * (1 + limit_pct), 2)

            df_temp['sold'] = df_temp.apply(
                lambda x: any(
                    [True if x[n] >= limit else False for n in ('open', 'high', 'low', 'close')]),
                axis=1
            )
            try:
                exit_date = df_temp[df_temp['sold']].index.values[0]
                exit_time = 'during'

                # check use what
                exit_price = limit
                if df_temp.ix[exit_date]['open'] >= limit:
                    exit_time = 'open'
                    exit_price = df_temp.ix[exit_date]['open']
                limit_hit = True
            except IndexError:
                # no stop loss hit
                exit_date = df_temp.index.values[-1]
                exit_time = 'close'
                exit_price = df_temp.ix[exit_date]['close']
                limit_hit = False
        else:
            limit = np.round(signal['close0'] * (1 - limit_pct), 2)
            df_temp['sold'] = df_temp['close'] <= limit

            df_temp['sold'] = df_temp.apply(
                lambda x: any(
                    [True if x[n] <= limit else False for n in ('open', 'high', 'low', 'close')]),
                axis=1
            )
            try:
                exit_date = df_temp[df_temp['sold']].index.values[0]

                # check use what
                exit_time = 'during'
                exit_price = limit
                if df_temp.ix[exit_date]['open'] <= limit:
                    exit_price = df_temp.ix[exit_date]['open']
                    exit_time = 'open'
                limit_hit = True
            except IndexError:
                # no stop loss hit
                exit_date = df_temp.index.values[-1]
                exit_time = 'close'
                exit_price = df_temp.ix[exit_date]['close']
                limit_hit = False

        loss_hits.append(limit_hit)
        exit_dates.append(exit_date)
        exit_times.append(exit_time)
        exit_prices.append(exit_price)

    df = df_signal1.copy()
    df['date1'] = exit_dates
    df['time1'] = exit_times
    df['close1'] = np.round(exit_prices, 2)
    df['holding'] = df['date1'] - df['date0']

    df['pct_chg'] = (df['close1'] - df['close0']) / df['close0']
    df['pct_chg'] = np.round(df.apply(
        lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg']
        , axis=1), 4
    )

    # for stock option quantity multiply
    df['sqm0'] = df.apply(lambda x: -1 if x['signal0'] == 'SELL' else 1, axis=1)
    df['sqm1'] = -df['sqm0']
    df['oqm0'] = 0
    df['oqm1'] = 0

    return df