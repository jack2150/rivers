import logging
import numpy as np
import pandas as pd
from research.strategy.trade.option_cs import get_cycle_strike

logger = logging.getLogger('views')


def create_order(df_signal, df_all, side=('follow', 'long', 'short'), cycle=0, strike=0):
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
    else:
        # sell is long put, buy is short put
        temp = df_signal2['signal0'].copy()
        df_signal2['signal0'] = df_signal2['signal1']
        df_signal2['signal1'] = temp

    signals = []
    for index, data in df_signal2.iterrows():
        try:
            option0, option1 = get_cycle_strike(
                df_all, data['date0'], data['date1'],
                'PUT', data['close0'], cycle, strike
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

            signals.append(data)
        except (KeyError, ValueError, IndexError):
            logger.info('Option not found, date: %s cycle: %s strike: %s' % (
                data['date0'].strftime('%Y-%m-%d'), cycle, strike
            ))
            # print 'not found'

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
