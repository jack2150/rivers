"""
Type: Month to month
Name: Calendar
Method: Enter at month days until month days
"""
import pandas as pd
from pandas.tseries.offsets import BDay


def handle_data(df):
    df0 = df.copy()

    df0['weekday'] = df0['date'].apply(lambda x: x.weekday() + 1)
    df0['week'] = df0['date'].apply(lambda x: x.weekofyear)
    df0['year'] = df0['date'].apply(lambda x: x.year)

    return df0


def create_signal(df, side=('buy', 'sell'), weekday0=0, bdays=0):
    if not 0 < weekday0 < 6:
        raise ValueError('Weekday must between 1-5')

    if bdays < 1:
        raise ValueError('Bdays must not greater than 0')

    df1 = df.copy()
    df2 = df.set_index('date')
    data = []
    signal0 = side.upper()
    signal1 = 'SELL' if side == 'buy' else 'BUY'

    # start split
    years = list(df1['year'].unique())
    weekdays = range(1, 5)

    for year in years:
        df_year = df2[df2['year'] == year]
        weeks = df_year['week'].unique()
        for week in weeks:
            date_str = '%s-%02d-%d' % (year, week, weekday0)
            start = pd.datetime.strptime(date_str, '%Y-%W-%w')
            stop = start + BDay(bdays)

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

