"""
Type: Option
Name: Day to Expire
Method: Hold X day until expire
"""
import numpy as np
import pandas as pd
from pandas.tseries.offsets import Day


def handle_data(df):
    return df


def create_signal(df, df_all,
                  dte=0, side=('buy', 'sell'), special=('Standard', 'Weekly')):
    if special == 'Standard':
        df_option = df_all.query('special == "Standard"')
    else:
        df_option = df_all

    if side == 'buy':
        signal0 = 'BUY'
        signal1 = 'SELL'
    else:
        signal0 = 'SELL'
        signal1 = 'BUY'

    df_dte = df_option.query('dte == %r' % dte)
    if len(df_dte) == 0:
        return pd.DataFrame(columns=[
            'date0', 'date1', 'signal0', 'signal1', 'close0', 'close1', 'holding', 'pct_chg'
        ])

    dte_dates = pd.to_datetime(np.sort(df_dte['date'].unique()))

    missing_dates = []
    for d0, d1 in zip(dte_dates[:-1], dte_dates[1:]):
        days = (d1 - d0).days

        # print x, y, days
        if days >= 28 * 2:
            next_day = d0 + Day(28 + 1)
            df_next = df[next_day == df['date']]
            if len(df_next):
                missing_dates.append(next_day)
            else:
                prev_day = d0 + Day(28 - 1)
                df_prev = df[prev_day == df['date']]

                if len(df_prev):
                    missing_dates.append(prev_day)

    if len(missing_dates):
        missing_dates = pd.to_datetime(missing_dates)
        dte_dates = pd.to_datetime(np.append(dte_dates, missing_dates))
        dte_dates = dte_dates.sort_values()

    # find exit date
    dates = list(df['date'])
    closes = df.set_index('date')['close']

    signals = []
    for i in np.arange(len(dte_dates)):
        date0 = dte_dates[i]
        date1 = date0 + Day(dte)
        # print date0, date1, date1 in dates

        prev = 1
        while date1 not in dates:
            date1 = date0 + Day(dte - prev)
            prev += 1

            if prev > 5:
                break

        if date1 not in dates:
            continue

        if prev < 4:  # found
            signals.append((
                date0, date1, signal0, signal1, closes[date0], closes[date1]
            ))

    df_signal = pd.DataFrame(signals, columns=[
        'date0', 'date1', 'signal0', 'signal1', 'close0', 'close1'
    ])

    df_signal['holding'] = df_signal['date1'] - df_signal['date0']
    df_signal['pct_chg'] = (df_signal['close1'] - df_signal['close0']) / df_signal['close0']

    # apply algorithm result
    df_signal['pct_chg'] = df_signal.apply(
        lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg'],
        axis=1
    )

    df_signal = df_signal.round({
        'pct_chg': 4
    })
    df_signal.reset_index(drop=True, inplace=True)

    return df_signal
