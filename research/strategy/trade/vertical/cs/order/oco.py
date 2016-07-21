import logging
import numpy as np
import pandas as pd
from scipy.stats import norm
from base.ufunc import ts
from data.option.day_iv.calc import today_iv, correct_prob
from research.strategy.trade.option_cs import get_cycle_strike

logger = logging.getLogger('views')


def reverse(x):
    return 'SELL' if x == 'BUY' else 'BUY'


def create_order(df_signal, df_stock, df_all,
                 name=('call', 'put'),
                 side=('follow', 'reverse', 'buy', 'sell'),
                 cycle=0, strike=0, wide=1,
                 limit_pct=0, stop_pct=0):
    """
    Vertical LIMIT option strategy, support follow, long, short
    :param df_signal: pd.DataFrame
    :param df_stock: pd.DataFrame
    :param df_all: pd.DataFrame
    :param name: str ('call', 'put')
    :param side: str ('follow', 'long', 'short')
    :param cycle: int (can only be positive)
    :param wide: int
    :param strike: int (negative ITM or positive OTM or zero closest ATM)
    :param limit_pct: int
    :param stop_pct: int
    :return: pd.DataFrame
    """
    if cycle < 0:
        raise ValueError('Cycle must be greater than -1')

    if wide < 1:
        raise ValueError('Wide must be greater than 0')

    df_signal0 = df_signal.copy()
    closes = df_stock[['date', 'close']].set_index('date')['close']

    if side == 'buy':
        df_signal0['signal0'] = 'BUY'
        df_signal0['signal1'] = 'SELL'
    elif side == 'sell':
        df_signal0['signal0'] = 'SELL'
        df_signal0['signal1'] = 'BUY'
    elif side == 'follow':
        if name == 'put':
            df_signal0['signal0'] = df_signal0['signal0'].apply(reverse)
            df_signal0['signal1'] = df_signal0['signal1'].apply(reverse)
    elif side == 'reverse':
        if name == 'call':
            df_signal0['signal0'] = df_signal0['signal0'].apply(reverse)
            df_signal0['signal1'] = df_signal0['signal1'].apply(reverse)

    signals = []
    for index, data in df_signal0.iterrows():
        try:
            option0a, option0b = get_cycle_strike(
                df_all, data['date0'], data['date1'],
                name.upper(), data['close0'], cycle, strike
            )

            option1a, option1b = get_cycle_strike(
                df_all, data['date0'], data['date1'],
                name.upper(), data['close0'], cycle, strike + wide
            )

            # df = pd.DataFrame([option0, option1])
            # print df.to_string(line_width=1000)
            df_code0 = df_all.query('option_code == %r & date >= %r & date <= %r' % (
                option0a['option_code'], data['date0'], data['date1']
            ))[['date', 'option_code', 'buy', 'sell']]
            df_code1 = df_all.query('option_code == %r & date >= %r & date <= %r' % (
                option1a['option_code'], data['date0'], data['date1']
            ))[['date', 'option_code', 'buy', 'sell']]

            # print df_code0.to_string(line_width=1000)
            # print df_code1.to_string(line_width=1000)
            df_join = pd.merge(df_code0, df_code1, on='date', suffixes=('0', '1'))

            if data['signal0'] == 'BUY':
                df_join['enter'] = df_join['buy0'] - df_join['sell1']
                df_join['exit'] = df_join['sell0'] - df_join['buy1']

                enter_price = df_join['enter'].iloc[0]
                if name == 'call':
                    max_profit = option1a['strike'] - option0a['strike'] - enter_price
                else:
                    max_profit = option0a['strike'] - option1a['strike'] - enter_price
                limit_price = enter_price + max_profit * (limit_pct / 100.0)
                df_join['limit'] = df_join['exit'] >= limit_price

                stop_price = enter_price * (stop_pct / 100.0)
                df_join['stop'] = df_join['exit'] <= stop_price
            else:
                df_join['enter'] = df_join['sell0'] - df_join['buy1']
                df_join['exit'] = df_join['buy0'] - df_join['sell1']

                enter_price = df_join['enter'].iloc[0]
                max_profit = enter_price
                limit_price = max_profit * (limit_pct / 100.0)
                df_join['limit'] = df_join['exit'] <= limit_price

                if name == 'call':
                    max_loss = option1a['strike'] - option0a['strike'] - enter_price
                else:
                    max_loss = option0a['strike'] - option1a['strike'] - enter_price

                stop_price = enter_price + max_loss * (stop_pct / 100.0)
                df_join['stop'] = df_join['exit'] >= stop_price

            # print option0a['strike'], option1a['strike'],
            # print enter_price, max_profit, limit_price
            # ts(df_join)
            # exit()

            df_oco = df_join[(df_join['limit']) | (df_join['stop'])]

            data['name'] = name.upper()
            data['code0'] = option0a['option_code']
            data['code1'] = option1a['option_code']
            data['strike0'] = option0a['strike']
            data['strike1'] = option1a['strike']
            if len(df_oco):
                exit_date = pd.to_datetime(df_oco['date'].iloc[0])
                data['date1'] = exit_date
                data['stock0'] = data['close0']
                data['stock1'] = closes[exit_date]

                if data['signal0'] == 'BUY':
                    data['price0a'] = option0a['buy']
                    data['price1a'] = -option1a['sell']
                    data['price0b'] = -df_oco['sell0'].iloc[0]
                    data['price1b'] = df_oco['buy1'].iloc[0]
                else:  # SELL
                    data['price0a'] = -option0a['sell']
                    data['price1a'] = option1a['buy']
                    data['price0b'] = df_oco['buy0'].iloc[0]
                    data['price1b'] = -df_oco['sell1'].iloc[0]
            else:
                data['stock0'] = data['close0']
                data['stock1'] = data['close1']
                if data['signal0'] == 'BUY':
                    data['price0a'] = option0a['buy']
                    data['price1a'] = -option1a['sell']
                    data['price0b'] = -option0b['sell']
                    data['price1b'] = option1b['buy']
                else:  # SELL
                    data['price0a'] = -option0a['sell']
                    data['price1a'] = option1a['buy']
                    data['price0b'] = option0b['buy']
                    data['price1b'] = -option1b['sell']

            signals.append(data)
        except (KeyError, ValueError, IndexError):
            logger.info('Option not found, date: %s cycle: %s strike: %s' % (
                data['date0'].strftime('%Y-%m-%d'), cycle, strike
            ))

    df = pd.DataFrame(signals)
    df['close0'] = df['price0a'] + df['price1a']
    df['close1'] = df['price0b'] + df['price1b']
    df = df[df['close0'] != 0]

    df['bp_effect'] = df.apply(
        lambda x: x['close0'] * 100 if x['signal0'] == 'BUY' else
        (abs(x['strike0'] - x['strike1']) + x['close0']) * 100,
        axis=1
    )
    df['net_chg'] = -df['close1'] - df['close0']
    df['pct_chg'] = (df['net_chg']) / np.abs(df['strike1'] - df['strike0'])

    df['holding'] = df['date1'] - df['date0']

    df['sqm0'] = 0
    df['sqm1'] = 0
    df['oqm0'] = df.apply(lambda x: -2 if x['signal0'] == 'SELL' else 2, axis=1)
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
    df_stock0 = df_stock.set_index('date')
    df_list = []
    for index, data in df_order.iterrows():
        df_both = df_all.query(
            '(option_code == %r | option_code == %r) & date >= %r  & date <= %r' % (
                data['code0'], data['code1'], data['date0'], data['date1']
            )
        )[['date', 'option_code', 'dte', 'sell', 'buy', 'strike']]

        df0 = df_both.query('option_code == %r' % data['code0'])
        df1 = df_both.query('option_code == %r' % data['code1'])
        df_join = pd.merge(df0, df1, on='date', suffixes=(0, 1))

        if data['signal0'] == 'BUY':
            first = df_join['buy0'] - df_join['sell1']
            remain = df_join['sell0'] - df_join['buy1']
            df_join['signal'] = ['BUY'] + ['SELL'] * len(remain[1:])
            df_join['option'] = [first.iloc[0]] + list(remain[1:])
        else:
            first = -df_join['sell0'] + df_join['buy1']
            remain = -df_join['buy0'] + df_join['sell1']
            df_join['signal'] = ['SELL'] + ['BUY'] * len(remain[1:])
            df_join['option'] = [first.iloc[0]] + list(remain[1:])

        df_join['pos_net'] = df_join['option'] - df_join['option'].iloc[0]
        df_join['pct_chg'] = df_join['pos_net'] / np.abs(df_join['option'].iloc[0]) + 0

        df_join = df_join.drop(['sell0', 'buy0', 'sell1', 'buy1', 'strike0', 'strike1', 'dte1'], axis=1)
        df_close = df_stock0[data['date0']:data['date1']]
        df_close = df_close[['close']].reset_index()
        df_both = pd.merge(df_join, df_close, on='date')
        df_both.rename(index=str, columns={'close': 'stock', 'dte0': 'dte'}, inplace=True)

        # today iv
        df_both['dte_iv'] = df_both.apply(
            lambda x: today_iv(df_iv, x['date'], x['dte']), axis=1
        )

        # create stage

        if data['name'] == 'CALL':
            if data['signal0'] == 'BUY':
                stages = {
                    'ml100': data['strike0'],
                    'even': data['strike0'] + data['close0'],
                    'mp100': data['strike1'],
                }
            else:
                stages = {
                    'mp100': data['strike0'],
                    'even': data['strike1'] + data['close0'],
                    'ml100': data['strike1'],
                }
        else:
            if data['signal0'] == 'BUY':
                stages = {
                    'ml100': data['strike0'],
                    'even': data['strike1'] + data['close0'],
                    'mp100': data['strike1'],
                }
            else:
                stages = {
                    'mp100': data['strike0'],
                    'even': data['strike0'] + data['close0'],
                    'ml100': data['strike1'],
                }

        for stage in ('ml100', 'even', 'mp100'):
            df_both[stage] = stages[stage]
            df_both['%s%%' % stage] = norm.cdf(df_both[stage], df_both['stock'], df_both['dte_iv'])
            df_both['%s%%' % stage] = df_both.apply(correct_prob, args=(stage,), axis=1)

        # calc stage probability

        # print df.to_string(line_width=1000)
        df_both = df_both.replace([np.inf, -np.inf], np.nan)
        df_both = df_both.fillna(0)

        df_both = df_both.round({
            'pos_net': 2,
            'pct_chg': 2,
            'dte_iv': 2,
            'ml100%': 2,
            'even%': 2,
            'mp100%': 2,
        })

        df_list.append(df_both)

    return df_list
