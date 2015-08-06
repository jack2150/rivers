"""
Type: Event Earning
Name: Earning Movement
Method: Enter before and exit after
"""
from django.db.models import Q
import itertools
from pandas import rolling_mean
import numpy as np
import pandas as pd
from data.models import Earning


def handle_data(df):
    symbol = df.ix[df.index.values[0]]['symbol']

    earnings = pd.DataFrame(list(Earning.objects.filter(
        Q(symbol=symbol) & (Q(status='Verified') | Q(status='Valid'))
    ).order_by('date_act').values()))
    earnings = earnings.set_index('date_act')

    # verify earnings
    s = [int(q[1:]) for q in earnings['quarter']]
    r = list(itertools.chain.from_iterable([range(1, 5) * int(np.ceil(len(earnings) / 4.0) + 1)]))
    if s != r[s[0] - 1:s[0] - 1 + len(s)]:
        raise LookupError('%s earning is missing quarter, need valid data' % symbol)

    date_act = list(earnings.index)
    df2 = df.copy()
    df2['earning'] = df2['date'].apply(lambda x: x in date_act)
    df2['release'] = df2.apply(
        lambda x: earnings.ix[x['date']]['release'] if x['earning'] else np.nan, axis=1
    )

    return df2


def create_signal(df, before=0, after=0, side=('BUY', 'SELL')):
    df_signal = df[df['earning']]

    dates0 = list()
    dates1 = list()
    closes0 = list()
    closes1 = list()
    for index, data in df_signal.iterrows():
        start = np.where(df['date'] == data['date'])[0][0] - before
        stop = np.where(df['date'] == data['date'])[0][0] + 1 + after

        # before market, during market
        if data['release'] in ('Before Market', 'During Market'):
            start = np.where(df['date'] == data['date'])[0][0] - 1 - before
            stop = np.where(df['date'] == data['date'])[0][0] + after

        dates0.append(df.ix[start]['date'])
        dates1.append(df.ix[stop]['date'])
        closes0.append(df.ix[start]['close'])
        closes1.append(df.ix[stop]['close'])
    else:
        df_signal['date0'] = dates0
        df_signal['date1'] = dates1
        df_signal['close0'] = closes0
        df_signal['close1'] = closes1

    df_signal['signal0'] = side
    df_signal['signal1'] = 'SELL' if side == 'BUY' else 'BUY'

    df_signal = df_signal.reindex_axis(
        ['date0', 'date1', 'signal0', 'signal1', 'close0', 'close1'], axis=1
    ).dropna()

    df_signal['holding'] = df_signal['date1'] - df_signal['date0']
    df_signal['pct_chg'] = (df_signal['close1'] - df_signal['close0']) / df_signal['close0']

    # apply algorithm result
    f = lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg']
    df_signal['pct_chg'] = df_signal.apply(f, axis=1)
    df_signal['pct_chg'] = df_signal['pct_chg']

    return df_signal.copy()
