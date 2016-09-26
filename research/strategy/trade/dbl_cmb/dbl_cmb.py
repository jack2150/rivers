import logging
import numpy as np
import pandas as pd
from scipy.stats import norm
from base.ufunc import ts
from data.option.day_iv.calc import today_iv, correct_prob
from research.strategy.trade.option_cask import get_price_ask
from research.strategy.trade.option_cs import get_cycle_strike as cs

logger = logging.getLogger('views')


def reverse(x):
    return 'SELL' if x == 'BUY' else 'BUY'


def create_order(df_signal, df_all,
                 side=('follow', 'reverse', 'buy', 'sell'),
                 cycle0=0, cycle1=0, pct0=0, pct1=0):
    """
    Single CALL option strategy, support follow, long, short
    :param df_signal: pd.DataFrame
    :param df_all: pd.DataFrame
    :param side: str ('follow', 'long', 'short')
    :param cycle0: int > 0
    :param cycle1: int > 0
    :param pct1: int
    :param pct0: int
    :return: pd.DataFrame
    """
    if cycle0 < 0 or cycle1 < 0:
        raise ValueError('Invalid cycle0 or cycle1, where cycle < 0')

    df_signal0 = df_signal.copy()

    if side == 'buy':
        df_signal0['signal0'] = 'BUY'
        df_signal0['signal1'] = 'SELL'
    elif side == 'sell':
        df_signal0['signal0'] = 'SELL'
        df_signal0['signal1'] = 'BUY'
    elif side == 'reverse':
        df_signal0['signal0'] = df_signal0['signal0'].apply(reverse)
        df_signal0['signal1'] = df_signal0['signal1'].apply(reverse)

    signals = []
    for index, data in df_signal0.iterrows():
        try:
            target0 = data['close0'] * (1 + (pct0 / 100.0))
            target1 = data['close0'] * (1 + (pct1 / 100.0))

            if side == 'buy':
                name0 = 'CALL'
                name1 = 'PUT'
                strike0 = 0
                strike1 = -1
            else:
                name0 = 'PUT'
                name1 = 'CALL'
                strike0 = -1
                strike1 = 0

            date0 = data['date0']
            date1 = data['date1']

            #target0 = 20
            #target1 = 20

            enter0f, exit0f = cs(df_all, date0, date1, name0, target0, cycle0, strike0)
            enter1f, exit1f = cs(df_all, date0, date1, name1, target1, cycle0, strike1)
            enter0b, exit0b = cs(df_all, date0, date1, name0, target0, cycle1, strike0)
            enter1b, exit1b = cs(df_all, date0, date1, name1, target1, cycle1, strike1)

            # df = pd.DataFrame([option0a, option0b, option1a, option1b])
            # ts(df)

            data['stock0'] = data['close0']
            data['stock1'] = data['close1']
            data['code0f'] = enter0f['option_code']
            data['code1f'] = enter1f['option_code']
            data['code0b'] = enter0b['option_code']
            data['code1b'] = enter1b['option_code']
            data['strike0'] = enter0f['strike']
            data['strike1'] = enter1f['strike']
            data['dte0'] = enter0f['dte']
            data['dte1'] = enter0b['dte']
            # buy sell are same
            data['enter0f'] = enter0f['buy']
            data['enter1f'] = -enter1f['sell']
            data['enter0b'] = -enter0b['sell']
            data['enter1b'] = enter1b['buy']
            data['exit0f'] = -exit0f['sell']
            data['exit1f'] = exit1f['buy']
            data['exit0b'] = exit0b['buy']
            data['exit1b'] = -exit1b['sell']

            signals.append(data)
        except (KeyError, ValueError, IndexError):
            logger.info('Not found, date: %s pct0: %s pct1: %s' % (
                data['date0'].strftime('%Y-%m-%d'), pct0, pct1
            ))

    df = pd.DataFrame(signals)
    df['close0'] = df['enter0f'] + df['enter1f'] + df['enter0b'] + df['enter1b']
    df['close1'] = df['exit0f'] + df['exit1f'] + df['exit0b'] + df['exit1b']
    df = df[df['close0'] != 0]

    df['bp_effect'] = df['stock0'] * 100
    df['net_chg'] = -df['close1'] - df['close0']
    df['pct_chg'] = df['net_chg'] / df['stock0']

    df['sqm0'] = 0
    df['sqm1'] = 0
    df['oqm0'] = df.apply(lambda x: -4 if x['signal0'] == 'SELL' else 4, axis=1)
    df['oqm1'] = -df['oqm0']

    df = df.round({
        'pct_chg': 4,
        'net_chg': 2
    })

    return df


def join_data(df_order, df_stock, df_all, df_iv):
    """
    Use for trade report view to check each trade
    :param df_order: pd.DataFrame
    :param df_stock: pd.DataFrame
    :param df_all: pd.DataFrame
    :param df_iv: pd.DataFrame
    :return: list
    """
    raise NotImplementedError('Not yet implemented')
