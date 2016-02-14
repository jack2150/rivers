"""
Type: Event Earning
Name: Earning Movement
Method: Enter before and exit after
"""
import pandas as pd
from research.algorithm.formula.event.earning.merge import merge_stock_earning


def handle_data(df, df_earning):
    df_merge = merge_stock_earning(df, df_earning)

    return df_merge


def create_signal(df, side=('buy', 'sell'), before=0, after=0):
    signals = []
    for index, data in df[~df['actual_date'].isnull()].iterrows():
        enter_index = index - before - 1
        exit_index = index + after
        if enter_index < 0 or exit_index > len(df):
            # print 'skip', data['date']
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
        'holding', 'pct_chg', 'earning', 'release'
    ]]

    return df_signal
