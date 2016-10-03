"""
Type: Month to month
Name: Calendar
Method: Enter at month days until month days
"""
import pandas as pd


def handle_data(df):
    df0 = df.copy()

    df0['year'] = df0['date'].apply(lambda x: x.year)

    return df0


def create_signal(df, side=('buy', 'sell'), month0=1, date0=1, month1=2, date1=1, cross_year=0):
    if not 0 < month0 < 13 or not 0 < month1 < 13:
        raise ValueError('Month must between 1-12')

    if not 0 < date0 < 32 or not 0 < date1 < 32:
        raise ValueError('Date must between 1-31')

    if cross_year > 4:
        raise ValueError('Year must not greater than 5')

    df1 = df.copy()
    df2 = df.set_index('date')
    data = []
    signal0 = side.upper()
    signal1 = 'SELL' if side == 'buy' else 'BUY'

    # start split
    years = list(df1['year'].unique())
    for year in years:
        start = pd.datetime(year, month0, date0)
        if month0 > month1:
            stop = pd.datetime(year + 1 + cross_year, month1, date1)
        else:
            stop = pd.datetime(year + cross_year, month1, date1)

        # print start, stop, stop - start
        df_current = df2[start:stop]
        if len(df_current) == 0:
            continue
        else:
            df_current = df_current.reset_index()

        first = df_current.iloc[0]
        last = df_current.iloc[len(df_current) - 1]
        data.append({
            'date0': first['date'],
            'date1': last['date'],
            'close0': first['close'],
            'close1': last['close'],
            'signal0': signal0,
            'signal1': signal1,
        })

    # create signal
    df_signal = pd.DataFrame(data)
    df_signal = df_signal[['date0', 'date1', 'signal0', 'signal1', 'close0', 'close1']]
    df_signal['holding'] = df_signal['date1'] - df_signal['date0']
    df_signal['pct_chg'] = df_signal.apply(
        lambda x: (
            (x['close1'] / x['close0']) - 1
            if x['signal0'] == 'BUY' else
            1 - (x['close1'] / x['close0'])
        ),
        axis=1
    )

    return df_signal.copy()

