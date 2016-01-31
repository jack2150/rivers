"""
Type: Option
Name: Option day to expire (DTE)
Method: Normal
"""
import calendar
from datetime import date
import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay, Day


def handle_data(df, dte=0):
    """
    1. find every third week in month
    2. use month minus day to get start day
    """
    first_date = df.ix[df.index.values[0]]['date']
    last_date = df.ix[df.index.values[-1]]['date']
    trading_dates = list(df['date'])
    start_dates = list()
    expire_dates = list()

    calendar.setfirstweekday(calendar.SUNDAY)

    # get expire date
    for year, month in df['date'].apply(lambda x: (x.year, x.month)).unique():
        c = calendar.monthcalendar(year, month)
        for w in c:
            if not any(w[1:6]):
                del c[c.index(w)]
        else:
            day = c[2][-2]

        expire_dates.append(date(year=year, month=month, day=day))

    # set start date in df
    for ex_date in expire_dates:
        start_day = pd.to_datetime(ex_date - Day(dte))

        while start_day not in trading_dates:
            if start_day > first_date:
                start_day = pd.to_datetime(start_day - BDay(1))
            else:
                start_dates.append(None)
                break
        else:
            start_dates.append(start_day)
    #print start_dates

    # set expire date in df
    for key, ex_day in enumerate(expire_dates):
        if not ex_day in trading_dates:
            p_day = pd.to_datetime(ex_day)
            while p_day not in trading_dates:
                if p_day < pd.to_datetime(last_date):
                    p_day = pd.to_datetime(p_day - BDay(1))
                else:
                    expire_dates[key] = None
                    break
            else:
                expire_dates[key] = p_day
    # drop none set
    for key, (sd, ed) in enumerate(zip(start_dates, expire_dates)):
        if not sd or not ed:
            del start_dates[start_dates.index(sd)]
            del expire_dates[expire_dates.index(ed)]

    if len(start_dates) != len(expire_dates):
        raise ValueError('Start dates and expire dates have different length.')

    #for s, e in zip(start_dates, expire_dates):
    #    print s, e

    df['enter'] = df['date'].apply(lambda x: x in start_dates)
    df['exit'] = df['date'].apply(lambda x: x in expire_dates)

    return df.copy()


def create_signal(df, side=('buy', 'sell')):
    df_enter = df[df['enter']]
    df_exit = df[df['exit']]
    df_enter.index = np.arange(df_enter['close'].count())
    df_exit.index = df_enter.index
    df_enter.columns = ['%s0' % c for c in df_enter.columns]
    df_exit.columns = ['%s1' % c for c in df_exit.columns]

    df2 = pd.concat([df_enter, df_exit], axis=1)
    if side == 'buy':
        df2['signal0'] = 'BUY'
        df2['signal1'] = 'SELL'
    else:
        df2['signal0'] = 'SELL'
        df2['signal1'] = 'BUY'

    df2 = df2.reindex_axis(
        ['date0', 'date1', 'signal0', 'signal1', 'close0', 'close1'], axis=1
    ).dropna()

    df2['holding'] = df2['date1'] - df2['date0']
    df2['pct_chg'] = (df2['close1'] - df2['close0']) / df2['close0']

    # apply algorithm result
    f = lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg']
    df2['pct_chg'] = df2.apply(f, axis=1)
    df2['pct_chg'] = df2['pct_chg']

    return df2.copy()


