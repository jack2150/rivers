"""
Type: Event Earning
Name: Earning Effect
Method: Enter earning trade using previous x days movement,
        if previous 5 days is up 2%, enter buy,
        if previous 5 days is down 2%, enter sell
        follow, manager know report result
        reverse, manager don't know result
"""
import pandas as pd
from research.algorithm.formula.event.earning.merge import merge_stock_earning


def handle_data(df, df_earning):
    df_merge = merge_stock_earning(df, df_earning)

    return df_merge


def create_signal(df, side=('follow', 'reverse'), percent=0, days=0):
    percent = abs(percent / 100.0)
    signals = []
    for index, data in df[~df['actual_date'].isnull()].iterrows():
        # print index, data
        day0_index = index - 1 - days
        day1_index = index - 1
        if day0_index < 0:
            continue

        day0_data = df.ix[day0_index]
        day1_data = df.ix[day1_index]
        pct_chg = 1 - (day1_data['close'] / day0_data['close'])

        if pct_chg >= percent:  # bull
            signal = 'buy'
        elif pct_chg <= -percent:
            signal = 'sell'
        else:
            continue

        # follow or reverse
        if side == 'reverse':
            signal = 'sell' if signal == 'buy' else 'buy'

        signals.append({
            'date0': day1_data['date'],
            'date1': data['date'],
            'signal0': signal.upper(),
            'signal1': 'SELL' if signal == 'buy' else 'BUY',
            'close0': day1_data['close'],
            'close1': data['close'],
            'earning': data['actual_date'],
            'release': data['release'],
            'previous': pct_chg
        })

    df_signal = pd.DataFrame(signals)

    df_signal['holding'] = df_signal['date1'] - df_signal['date0']
    # apply algorithm result
    df_signal['pct_chg'] = (df_signal['close1'] - df_signal['close0']) / df_signal['close0']
    df_signal['pct_chg'] = df_signal.apply(
        lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg'],
        axis=1
    )

    df_signal = df_signal[[
        'date0', 'date1', 'signal0', 'signal1', 'close0', 'close1',
        'holding', 'pct_chg', 'earning', 'release', 'previous'
    ]]

    return df_signal
