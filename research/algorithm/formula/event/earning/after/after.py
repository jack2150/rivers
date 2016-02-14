"""
Type: Event Earning
Name: Earning Effect
Method: Enter after earning move up/down percent
        then enter buy or sell for a period
"""
import pandas as pd
from research.algorithm.formula.event.earning.merge import merge_stock_earning


def handle_data(df, df_earning, move=('up', 'down'), percent=0):
    percent = abs(percent)

    df_merge = merge_stock_earning(df, df_earning)
    df_merge['pct_chg'] = df_merge['close'].pct_change()

    if move == 'up':
        df_merge['enter0'] = df_merge['pct_chg'] >= percent / 100.0
    else:
        df_merge['enter0'] = df_merge['pct_chg'] <= -percent / 100.0

    df_merge['enter1'] = ~df_merge['actual_date'].isnull()

    df_merge['enter'] = df_merge['enter0'] & df_merge['enter1']

    return df_merge


def create_signal(df, side=('buy', 'sell'), days=0):
    signals = []
    for index, data in df[df['enter']].iterrows():
        enter_index = index
        exit_index = index + days

        if exit_index > len(df):
            continue

        enter_data = df.loc[enter_index]
        exit_data = df.loc[exit_index]

        signals.append({
            'date0': enter_data['date'],
            'date1': exit_data['date'],
            'signal0': side.upper(),
            'signal1': 'SELL' if side == 'buy' else 'BUY',
            'close0': enter_data['close'],
            'close1': exit_data['close'],
            'earning': data['actual_date'],
            'release': data['release'],
            'move': data['pct_chg']
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
        'holding', 'pct_chg', 'earning', 'release', 'move'
    ]]

    return df_signal
