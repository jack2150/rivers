import numpy as np


def create_order(df_signal, df_stock, profit_pct=0, loss_pct=0):
    """
    Trade stock with stop loss order
    :param df_signal: DataFrame
    :param df_stock: DataFrame
    :param profit_pct:
    :param loss_pct:
    :return: DataFrame
    """
    df0 = df_stock.copy()

    limit_pct = profit_pct / 100.0
    stop_loss_pct = loss_pct / 100.00
    order_hits = list()
    exit_dates = list()
    exit_times = list()
    exit_prices = list()

    for index, signal in df_signal.iterrows():
        df_temp = df0.ix[signal['date0']:signal['date1']][1:]

        limit_hit = False
        stop_loss_hit = False
        exit_price = 0
        if signal['signal0'] == 'BUY':
            """
            BUY Section
            """
            limit = np.round(signal['close0'] * (1 + limit_pct), 2)
            stop_loss = np.round(signal['close0'] * (1 - stop_loss_pct), 2)

            df_temp['sold1'] = df_temp.apply(
                lambda x: any(
                    [True if x[n] >= limit else False for n in ('open', 'high', 'low', 'close')]
                ),
                axis=1
            )
            df_temp['sold2'] = df_temp.apply(
                lambda x: any(
                    [True if x[n] <= stop_loss else False for n in ('open', 'high', 'low', 'close')]
                ),
                axis=1
            )
            df_temp['sold'] = df_temp['sold1'] | df_temp['sold2']

            # print df_temp.to_string(line_width=300)

            try:
                exit_date = df_temp[df_temp['sold']].index.values[0]
                exit_time = 'during'

                sold1 = df_temp.ix[exit_date]['sold1']
                sold2 = df_temp.ix[exit_date]['sold2']

                # check use what
                if sold1 and not sold2:
                    limit_hit = True
                    exit_price = limit
                    if df_temp.ix[exit_date]['open'] >= limit:
                        exit_time = 'open'
                        exit_price = df_temp.ix[exit_date]['open']
                elif (not sold1 and sold2) or (sold1 and sold2):
                    stop_loss_hit = True
                    exit_price = stop_loss
                    if df_temp.ix[exit_date]['open'] <= stop_loss:
                        exit_time = 'open'
                        exit_price = df_temp.ix[exit_date]['open']
            except IndexError:
                # no stop loss hit
                exit_date = df_temp.index.values[-1]
                exit_time = 'close'
                exit_price = df_temp.ix[exit_date]['close']
                limit_hit = False
        else:
            """
            SELL Section
            """
            limit = np.round(signal['close0'] * (1 - limit_pct), 2)
            stop_loss = np.round(signal['close0'] * (1 + stop_loss_pct), 2)

            df_temp['sold1'] = df_temp.apply(
                lambda x: any(
                    [True if x[n] <= limit else False for n in ('open', 'high', 'low', 'close')]
                ),
                axis=1
            )
            df_temp['sold2'] = df_temp.apply(
                lambda x: any(
                    [True if x[n] >= stop_loss else False for n in ('open', 'high', 'low', 'close')]
                ),
                axis=1
            )
            df_temp['sold'] = df_temp['sold1'] | df_temp['sold2']

            try:
                exit_date = df_temp[df_temp['sold']].index.values[0]

                sold1 = df_temp.ix[exit_date]['sold1']
                sold2 = df_temp.ix[exit_date]['sold2']

                # check use what
                exit_time = 'during'
                if sold1 and not sold2:
                    limit_hit = True
                    exit_price = limit
                    if df_temp.ix[exit_date]['open'] <= limit:
                        exit_time = 'open'
                        exit_price = df_temp.ix[exit_date]['open']
                elif (not sold1 and sold2) or (sold1 and sold2):
                    stop_loss_hit = True
                    exit_price = stop_loss
                    if df_temp.ix[exit_date]['open'] >= stop_loss:
                        exit_time = 'open'
                        exit_price = df_temp.ix[exit_date]['open']
            except IndexError:
                # no stop loss hit
                exit_date = df_temp.index.values[-1]
                exit_time = 'close'
                exit_price = df_temp.ix[exit_date]['close']
                limit_hit = False

        if limit_hit:
            order_hits.append('limit')
        elif stop_loss_hit:
            order_hits.append('stop loss')
        else:
            order_hits.append('normal')

        exit_dates.append(exit_date)
        exit_times.append(exit_time)
        exit_prices.append(exit_price)

    df = df_signal.copy()
    df['date1'] = exit_dates
    df['time1'] = exit_times
    df['order'] = order_hits
    df['close1'] = np.round(exit_prices, 2)
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