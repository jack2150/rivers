import numpy as np
import pandas as pd


def create_order(df_signal, df_stock, side=('follow', 'reverse', 'buy', 'sell'), percent=0):
    """
    Trade stock with trailing stop loss order
    :param df_signal: DataFrame
    :param df_stock: DataFrame
    :param side: str
    :param percent: float
    :return: DataFrame
    """
    df = df_stock.copy()

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

    trailing_stop = []
    for index, signal in df_signal1.iterrows():
        df_temp = df.ix[signal['date0']:signal['date1']][1:]

        if signal['signal0'] == 'BUY':
            highest = df_temp['high'].iloc[0]
            prices = [highest]
            for high in df_temp['high'][1:]:
                if high > highest:
                    highest = high
                    prices.append(highest)
                else:
                    prices.append(highest)
            df_temp['highest'] = prices
            df_temp['stop'] = np.round(df_temp['highest'] * (1 - percent / 100.0), 2)

            df_temp['sold'] = df_temp.apply(
                lambda x: any(
                    [1 if x[n] <= x['stop'] else 0 for n in ('open', 'high', 'low', 'close')]),
                axis=1
            )

            try:
                row = df_temp[df_temp['sold']].iloc[0]
                exit_date = df_temp[df_temp['sold']].index.values[0]
                exit_time = 'during'

                # check use what
                exit_price = row['stop']
                if row['open'] <= row['stop']:
                    exit_time = 'open'
                    exit_price = row['open']
                stop_hit = True
            except IndexError:
                # no stop loss hit
                exit_date = df_temp.index.values[-1]
                exit_time = 'close'
                exit_price = df_temp.ix[exit_date]['close']
                stop_hit = False
        else:
            lowest = df_temp['low'].iloc[0]
            prices = [lowest]
            for low in df_temp['low'][1:]:
                if low < lowest:
                    lowest = low
                    prices.append(lowest)
                else:
                    prices.append(lowest)
            df_temp['lowest'] = prices
            df_temp['stop'] = np.round(df_temp['lowest'] * (1 + percent / 100.0), 2)

            df_temp['sold'] = df_temp.apply(
                lambda x: any(
                    [1 if x[n] >= x['stop'] else 0 for n in ('open', 'high', 'low', 'close')]),
                axis=1
            )

            try:
                row = df_temp[df_temp['sold']].iloc[0]
                exit_date = df_temp[df_temp['sold']].index.values[0]
                exit_time = 'during'

                # check use what
                exit_price = row['stop']
                if row['open'] >= row['stop']:
                    exit_time = 'open'
                    exit_price = row['open']
                stop_hit = True
            except IndexError:
                # no stop loss hit
                exit_date = df_temp.index.values[-1]
                exit_time = 'close'
                exit_price = df_temp.ix[exit_date]['close']
                stop_hit = False

        trailing_stop.append({
            'exit_date': exit_date,
            'exit_time': exit_time,
            'exit_price': exit_price,
            'stop_hit': stop_hit,
        })

    df_result = pd.DataFrame(trailing_stop)
    df_trade = df_signal1.copy()
    """:type: pd.DataFrame"""

    df_trade['date1'] = df_result['exit_date']
    df_trade['close1'] = df_result['exit_price']
    df_trade['during'] = df_result['exit_time']
    df_trade['holding'] = df_trade['date1'] - df_trade['date0']
    df_trade['pct_chg'] = (df_trade['close1'] - df_trade['close0']) / df_trade['close0']
    df_trade['pct_chg'] = np.round(
        df_trade.apply(
            lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg']
            , axis=1
        ), 4
    )

    return df_trade
