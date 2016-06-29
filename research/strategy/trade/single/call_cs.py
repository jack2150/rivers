import logging

import numpy as np
import pandas as pd
from scipy.stats import norm

from data.option.day_iv.calc import today_iv, correct_prob
from research.strategy.trade.option_cs import get_cycle_strike

logger = logging.getLogger('views')


def create_order(df_signal, df_all, side=('follow', 'reverse', 'long', 'short'), cycle=0, strike=0):
    """
    Single CALL option strategy, support follow, long, short
    :param df_signal: pd.DataFrame
    :param df_all: pd.DataFrame
    :param side: str ('follow', 'long', 'short')
    :param cycle: int (can only be positive)
    :param strike: int (negative ITM or positive OTM or zero closest ATM)
    :return:
    """
    df_signal2 = df_signal.copy()

    if side == 'long':
        df_signal2['signal0'] = 'BUY'
        df_signal2['signal1'] = 'SELL'
    elif side == 'short':
        df_signal2['signal0'] = 'SELL'
        df_signal2['signal1'] = 'BUY'
    elif side == 'reverse':
        temp = df_signal2['signal0'].copy()
        df_signal2['signal0'] = df_signal2['signal1']
        df_signal2['signal1'] = temp

    signals = []
    for index, data in df_signal2.iterrows():
        try:
            option0, option1 = get_cycle_strike(
                df_all, data['date0'], data['date1'],
                'CALL', data['close0'], cycle, strike
            )

            # df = pd.DataFrame([option0, option1])
            # print df.to_string(line_width=1000)

            data['option_code'] = option0['option_code']
            if data['signal0'] == 'BUY':
                data['close0'] = option0['ask']
                data['close1'] = option1['bid']
            else:  # SELL
                data['close0'] = option0['bid']
                data['close1'] = option1['ask']

            # check no zero bid/ask
            if data['close0'] < 0.01:
                continue

            signals.append(data)
        except (KeyError, ValueError, IndexError):
            logger.info('Option not found, date: %s cycle: %s strike: %s' % (
                data['date0'].strftime('%Y-%m-%d'), cycle, strike
            ))

    df = pd.DataFrame(signals)
    df['pct_chg'] = (df['close1'] - df['close0']) / df['close0']
    df['pct_chg'] = np.round(df.apply(
        lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg']
        , axis=1),
        4
    )

    df['sqm0'] = 0
    df['sqm1'] = 0
    df['oqm0'] = df.apply(lambda x: -1 if x['signal0'] == 'SELL' else 1, axis=1)
    df['oqm1'] = -df['oqm0']

    return df


def join_data(df_trade, df_stock, df_all, df_iv):
    """
    Use for trade report view to check each trade
    :param df_trade: pd.DataFrame
    :param df_stock: pd.DataFrame
    :param df_all: pd.DataFrame
    :param df_iv: pd.DataFrame
    :return: list
    """
    df_stock0 = df_stock.set_index('date')
    df_list = []
    for index, data in df_trade.iterrows():
        df0 = df_all.query(
            'option_code == %r & date >= %r  & date <= %r' % (
                data['option_code'], data['date0'], data['date1']
            )
        )[['date', 'option_code', 'dte', 'bid', 'ask', 'strike']]

        df0.insert(6, 'signal', data['signal0'])
        if data['signal0'] == 'BUY':
            column = 'ask'
            exit_price = df0['bid'].iloc[-1]
            multiply = 1
        else:  # sell
            column = 'bid'
            exit_price = df0['ask'].iloc[-1]
            multiply = -1

        df0['option'] = df0[column]
        df0['option'].iloc[-1] = exit_price
        df0['signal'].iloc[-1] = data['signal1']
        df0['pos_net'] = df0['option'] - df0['option'].iloc[0]
        df0['pos_chg'] = df0['pos_net'] / df0['option'].iloc[0] * multiply + 0

        df0 = df0.drop(['bid', 'ask'], axis=1)
        strike = df0.iloc[0]['strike']
        df1 = df_stock0[data['date0']:data['date1']]
        df1 = df1[['close']].reset_index()
        df = pd.merge(df0, df1, on='date')
        df.rename(index=str, columns={'close': 'stock'}, inplace=True)

        # today iv
        df['dte_iv'] = df.apply(
            lambda x: today_iv(df_iv, x['date'], x['dte']),
            axis=1
        )
        # df['std1-'] = df['stock'] * (1 - df['dte_iv'] / 100.0)
        # df['std1+'] = df['stock'] * (1 + df['dte_iv'] / 100.0)

        # create stage
        if data['signal0'] == 'BUY':
            stage0 = 'ml'
            stage1 = 'even'
            stage2 = 'p100'
        else:
            stage0 = 'mp'
            stage1 = 'even'
            stage2 = 'ml100'

        # calc stage probability
        df[stage0] = strike
        df['%s%%' % stage0] = norm.cdf(df[stage0], df['stock'], df['dte_iv'])
        df['%s%%' % stage0] = df.apply(correct_prob, args=(stage0, ), axis=1)
        df[stage1] = strike + data['close0']
        df['%s%%' % stage1] = norm.cdf(df[stage1], df['stock'], df['dte_iv'])
        df['%s%%' % stage1] = df.apply(correct_prob, args=(stage1,), axis=1)
        df[stage2] = strike + (data['close0'] * 2)
        df['%s%%' % stage2] = norm.cdf(df[stage1], df['stock'], df['dte_iv'])
        df['%s%%' % stage2] = df.apply(correct_prob, args=(stage2,), axis=1)

        df = df.round({
            'pos_chg': 2,
            '%s%%' % stage0: 2,
            '%s%%' % stage1: 2,
            '%s%%' % stage2: 2,
            'dte_iv': 2,
            # 'std1-': 2,
            # 'std1+': 2,
        })

        # print df.to_string(line_width=1000)
        assert data['close1'] == df['option'].iloc[-1]

        df_list.append(df)

    return df_list





