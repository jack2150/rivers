import numpy as np
import pandas as pd
from base.ufunc import ts, ds


def create_order(df_signal, df_stock, side=('follow', 'reverse', 'buy', 'sell'),
                 profit_pct0=0, loss_pct0=0, profit_pct1=0, loss_pct1=0):
    """
    Trade stock with stop loss order
    :param df_signal: DataFrame
    :param df_stock: DataFrame
    :param side: str
    :param profit_pct0: int
    :param loss_pct0: int
    :param profit_pct1: int
    :param loss_pct1: int
    :return: DataFrame
    """
    df0 = df_stock.set_index('date').copy()

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

    limit_pct0 = profit_pct0 / 100.0
    stop_loss_pct0 = loss_pct0 / 100.00
    limit_pct1 = profit_pct1 / 100.0
    stop_loss_pct1 = profit_pct1 / 100.0
    data = {
        'order_hits0': [],
        'order_hits1': [],
        'exit_dates0': [],
        'exit_dates1': [],
        'exit_times0': [],
        'exit_times1': [],
        'exit_prices0': [],
        'convert_price0': [],
        'convert_price1': [],
        'pct_chg0.5': [],
        'pct_chg1': [],
    }

    for index, signal in df_signal1.iterrows():
        df_temp = df0.ix[signal['date0']:signal['date1']] # [1:]

        enter_price = signal['close0']
        if signal['signal0'] == 'BUY':
            """
            BUY Section
            """
            exit_date0, exit_price0, exit_time0, limit_hit0, stop_loss_hit0 = oco_buy(
                df_temp, signal['close0'], limit_pct0, stop_loss_pct0
            )

            exit_date1 = None
            exit_time1 = ''
            convert0 = 0
            convert1 = 0
            pct_chg05 = 0
            pct_chg1 = 0
            limit_hit1 = False
            stop_loss_hit1 = False
            normal = False
            if stop_loss_hit0:
                df_cont = df_temp[exit_date0:]
                exit_date1, exit_price1, exit_time1, limit_hit1, stop_loss_hit1 = oco_sell(
                    df_cont, exit_price0, limit_pct1, stop_loss_pct1
                )

                if not (limit_hit1 and stop_loss_hit1):
                    normal = True

                exit_date0, exit_date1 = exit_date1, exit_date0
                exit_time0, exit_time1 = exit_time1, exit_time0
                convert0 = exit_price0
                convert1 = exit_price1

                pct_chg05 = (convert0 - enter_price) / enter_price
                pct_chg1 = (convert0 - convert1) / convert0
                exit_price0 = convert0 * (1 + pct_chg1)
                # ts(df_temp)
        else:
            """
            SELL Section
            """
            exit_date0, exit_price0, exit_time0, limit_hit0, stop_loss_hit0 = oco_sell(
                df_temp, signal['close0'], limit_pct0, stop_loss_pct0
            )

            exit_date1 = None
            exit_time1 = ''
            convert0 = 0
            convert1 = 0
            pct_chg05 = 0
            pct_chg1 = 0
            limit_hit1 = False
            stop_loss_hit1 = False
            normal = False
            if stop_loss_hit0:
                df_cont = df_temp[exit_date0:]
                exit_date1, exit_price1, exit_time1, limit_hit1, stop_loss_hit1 = oco_buy(
                    df_cont, exit_price0, limit_pct1, stop_loss_pct1
                )

                if not (limit_hit1 and stop_loss_hit1):
                    normal = True

                exit_date0, exit_date1 = exit_date1, exit_date0
                exit_time0, exit_time1 = exit_time1, exit_time0
                convert0 = exit_price0
                convert1 = exit_price1

                pct_chg05 = -(convert0 - enter_price) / enter_price
                pct_chg1 = -(convert0 - convert1) / convert0
                exit_price0 = convert0 * (1 + pct_chg1)

        if limit_hit0:
            data['order_hits0'].append('limit')
        elif stop_loss_hit0:
            data['order_hits0'].append('stop loss')
        else:
            data['order_hits0'].append('normal')

        if limit_hit1:
            data['order_hits1'].append('limit')
        elif stop_loss_hit1:
            data['order_hits1'].append('stop loss')
        elif normal:
            data['order_hits1'].append('normal')
        else:
            data['order_hits1'].append('')

        data['exit_dates0'].append(exit_date0)
        data['exit_dates1'].append(exit_date1)
        data['exit_times0'].append(exit_time0)
        data['exit_times1'].append(exit_time1)
        data['exit_prices0'].append(exit_price0)
        data['convert_price0'].append(convert0)  # todo: wrong
        data['convert_price1'].append(convert1)
        data['pct_chg0.5'].append(pct_chg05)
        data['pct_chg1'].append(pct_chg1)

    df = df_signal1.copy()
    df['date0.5'] = pd.to_datetime(data['exit_dates1'])  # todo: need change
    df['date1'] = data['exit_dates0']
    df['time0'] = data['exit_times0']
    df['time1'] = data['exit_times1']
    df['order0'] = data['order_hits0']
    df['order1'] = data['order_hits1']
    df['convert0'] = np.round(data['convert_price0'], 2)
    df['convert1'] = np.round(data['convert_price1'], 2)
    df['close1'] = np.round(data['exit_prices0'], 2)
    df['holding'] = df['date1'] - df['date0']
    df['pct_chg0.5'] = data['pct_chg0.5']
    df['pct_chg1'] = data['pct_chg1']

    df['pct_chg'] = (df['close1'] - df['close0']) / df['close0']
    df['pct_chg'] = np.round(df.apply(
        lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg']
        , axis=1), 4
    )

    # order columns
    df = df[[
        'date0', 'date0.5', 'date1', 'signal0', 'signal1', 'holding',
        'time0', 'order0', 'time1', 'order1', 'close0', 'close1', 'convert0', 'convert1',
        'pct_chg0.5', 'pct_chg1', 'pct_chg',
    ]]

    # for stock option quantity multiply
    df['sqm0'] = df.apply(lambda x: -1 if x['signal0'] == 'SELL' else 1, axis=1)
    df['sqm1'] = -df['sqm0']
    df['oqm0'] = 0
    df['oqm1'] = 0

    # round data columns
    df = df.round({
        'pct_chg0.5': 4,
        'pct_chg1': 4,
    })

    return df


def oco_sell(df_temp, enter_price, limit_pct, stop_loss_pct):
    """

    :param signal:
    :param df_temp:
    :param enter_price:
    :param limit_pct:
    :param stop_loss_pct:
    :return:
    """
    exit_price0 = 0
    limit_hit0 = False
    stop_loss_hit0 = False

    limit = np.round(enter_price * (1 - limit_pct), 2)
    stop_loss = np.round(enter_price * (1 + stop_loss_pct), 2)
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
        exit_date0 = df_temp[df_temp['sold']].index.values[0]

        sold1 = df_temp.ix[exit_date0]['sold1']
        sold2 = df_temp.ix[exit_date0]['sold2']

        # check use what
        exit_time0 = 'during'
        if sold1 and not sold2:
            limit_hit0 = True
            exit_price0 = limit
            if df_temp.ix[exit_date0]['open'] <= limit:
                exit_time0 = 'open'
                exit_price0 = df_temp.ix[exit_date0]['open']
        elif (not sold1 and sold2) or (sold1 and sold2):
            stop_loss_hit0 = True
            exit_price0 = stop_loss
            if df_temp.ix[exit_date0]['open'] >= stop_loss:
                exit_time0 = 'open'
                exit_price0 = df_temp.ix[exit_date0]['open']
    except IndexError:
        # no stop loss hit
        exit_date0 = df_temp.index.values[-1]
        exit_time0 = 'close'
        exit_price0 = df_temp.ix[exit_date0]['close']
        limit_hit0 = False

    return exit_date0, exit_price0, exit_time0, limit_hit0, stop_loss_hit0


def oco_buy(df_temp, enter_price, limit_pct, stop_loss_pct):
    """

    :param df_temp:
    :param enter_price:
    :param limit_pct:
    :param stop_loss_pct:
    :return:
    """
    limit_hit = False
    stop_loss_hit = False
    exit_price = 0

    limit = np.round(enter_price * (1 + limit_pct), 2)
    stop_loss = np.round(enter_price * (1 - stop_loss_pct), 2)
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
    # ts(df_temp)
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

    return exit_date, exit_price, exit_time, limit_hit, stop_loss_hit


def join_data(df_trade, df_stock):
    """
    Join df_trade data into daily trade data
    :param df_trade: pd.DataFrame
    :param df_stock: pd.DataFrame
    :return: list
    """
    raise NotImplemented('Not yet implemented')

