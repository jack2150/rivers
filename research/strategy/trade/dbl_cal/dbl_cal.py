import logging
import numpy as np
import pandas as pd
from scipy.stats import norm
from data.option.day_iv.calc import today_iv, correct_prob
from research.strategy.trade.option_cs import get_cycle_strike

logger = logging.getLogger('views')


def create_order(df_signal, df_stock, df_all,
                 name0=('CALL', 'PUT'), name1=('CALL', 'PUT'),
                 side=('BUY', 'SELL'),
                 dte0=0, dte1=0,
                 percent0=0, percent1=1):
    if dte0 >= dte1:
        raise ValueError('Dte0 cannot greater or equal dte1')

    closes = df_stock[['date', 'close']].set_index('date')['close']
    df_standard = df_all.query('special == "Standard"')

    trades = []
    for index, data in df_signal.iterrows():
        enter_date = data['date0']
        df_date0 = df_standard.query('date == %r' % data['date0'])
        dtes = np.sort(df_date0['dte'].unique())

        # get cycles
        try:
            cycle0 = dtes[dtes >= dte0 - 1][0]
            cycle1 = dtes[dtes >= dte1][0]
        except IndexError:
            print 'no enough cycles: %s' % dtes
            continue

        # get duplicated strikes
        df_dte0 = df_date0.query('dte == %r | dte == %r' % (cycle0, cycle1))

        # duplicate need both call and put
        group = df_dte0.groupby('strike')['strike'].count()
        strikes = np.sort(group[group == 4].index)

        # get left and right strike
        target0 = data['close0'] * (1 - percent0 / 100.0)
        target1 = data['close0'] * (1 + percent1 / 100.0)

        try:
            strike0 = strikes[strikes <= target0][-1]
            strike1 = strikes[strikes >= target1][0]
        except IndexError:
            continue

        # print target0, data['close0'], target1
        # print strike0, '---', strike1
        # enter option
        query = 'strike == %r & name == %r & dte == %r'
        enter0f = df_dte0.query(query % (strike0, name0, cycle0)).iloc[0]
        enter0b = df_dte0.query(query % (strike0, name0, cycle1)).iloc[0]
        enter1f = df_dte0.query(query % (strike1, name1, cycle0)).iloc[0]
        enter1b = df_dte0.query(query % (strike1, name1, cycle1)).iloc[0]

        # exit option
        exit_date = data['date1']
        df_date1 = df_standard.query('date == %r' % exit_date)
        try:
            exit0f = df_date1.query('option_code == %r' % enter0f['option_code']).iloc[0]
            exit0b = df_date1.query('option_code == %r' % enter0b['option_code']).iloc[0]
            exit1f = df_date1.query('option_code == %r' % enter1f['option_code']).iloc[0]
            exit1b = df_date1.query('option_code == %r' % enter1b['option_code']).iloc[0]
        except IndexError:
            continue

        if side == 'BUY':
            signal0 = 'BUY'
            signal1 = 'SELL'

            trades.append((
                enter_date, exit_date, signal0, signal1,
                cycle0, cycle1, name0, name1,
                enter0f['option_code'], enter1f['option_code'],
                enter0b['option_code'], enter1b['option_code'],
                strike0, strike1,
                -enter0f['sell'], -enter1f['sell'], enter0b['buy'], enter1b['buy'],
                -exit0f['buy'], -exit1f['buy'], exit0b['sell'], exit1b['sell'],
                data['close0'], data['close1']
            ))
        else:
            signal0 = 'SELL'
            signal1 = 'BUY'

            trades.append((
                enter_date, exit_date, signal0, signal1,
                cycle0, cycle1, name0, name1,
                enter0f['option_code'], enter1f['option_code'],
                enter0b['option_code'], enter1b['option_code'],
                strike0, strike1,
                enter0f['buy'], enter1f['buy'], -enter0b['sell'], -enter1b['sell'],
                exit0f['sell'], exit1f['sell'], -exit0b['buy'], -exit1b['buy'],
                data['close0'], data['close1']
            ))

    # make df
    df_trade = pd.DataFrame(trades, columns=[
        'date0', 'date1', 'signal0', 'signal1',
        'dte0', 'dte1', 'name0', 'name1',
        'option0f', 'option1f', 'option0b', 'option1b',
        'strike0', 'strike1',
        'enter0f', 'enter1f', 'enter0b', 'enter1b',
        'exit0f', 'exit1f', 'exit0b', 'exit1b',
        'stock0', 'stock1'
    ])

    df_trade['close0'] = (
        df_trade['enter0f'] + df_trade['enter1f'] + df_trade['enter0b'] + df_trade['enter1b']
    )
    df_trade['close1'] = (
        df_trade['exit0f'] + df_trade['exit1f'] + df_trade['exit0b'] + df_trade['exit1b']
    )

    # buy and sell exact same
    df_trade['net_chg'] = df_trade['close1'] - df_trade['close0']

    df_trade['pct_chg'] = df_trade['net_chg'] / np.abs(
        df_trade['enter0b'] + df_trade['enter1b']
    )

    # remove no use column
    df_trade = df_trade.round({
        'close0': 2,
        'close1': 2,
        'net_chg': 2,
        'pct_chg': 4
    })

    df_trade['holding'] = df_trade['date1'] - df_trade['date0']

    # for stock option quantity multiply
    df_trade['sqm0'] = 0
    df_trade['sqm1'] = 0
    df_trade['oqm0'] = 1
    df_trade['oqm1'] = -1

    return df_trade


def join_data(df_order, df_stock, df_all, df_iv):
    """
    :param df_order: pd.DataFrame
    :param df_stock: pd.DataFrame
    :param df_all: pd.DataFrame
    :param df_iv: pd.DataFrame
    :return: list
    """
    df_stock0 = df_stock.set_index('date')['close']
    keys = ('option0f', 'option1f', 'option0b', 'option1b')
    dtes = ('dte0f', 'dte1f', 'dte0b', 'dte1b')

    if df_order['signal0'].iloc[0] == 'BUY':
        enters = ('sell', 'sell', 'buy', 'buy')
        exits = ('buy', 'buy', 'sell', 'sell')
    else:
        enters = ('buy', 'buy', 'sell', 'sell')
        exits = ('sell', 'sell', 'buy', 'buy')

    df_list = []
    for i in np.arange(len(df_order)):
        data = df_order.ix[i]
        query = []
        for key in keys:
            query.append('option_code == %r' % data[key])

        query = ' | '.join(query)

        df_current = df_all.query(
            'date >= %r & date <= %r & (%s)' % (data['date0'], data['date1'], query)
        )

        df_codes = []
        for key, dte, signal0, signal1 in zip(keys, dtes, enters, exits):
            df_code = df_current.query('option_code == %r' % data[key]).sort_values('date')

            df_option = df_code[['date', 'dte']].copy()
            if signal0 == 'buy':
                df_option[signal1] = [df_code[signal0].iloc[0]] + list(-df_code[signal1][1:])
            else:
                df_option[signal1] = [-df_code[signal0].iloc[0]] + list(df_code[signal1][1:])

            df_option = df_option.set_index('date')
            df_option.columns = [dte, key]

            # print df_option
            df_codes.append(df_option)

        df = pd.concat(df_codes, axis=1)
        """:type: pd.DataFrame"""
        df['stock'] = df_stock0[data['date0']:data['date1']]
        df['strike0'] = data['strike0']
        df['strike1'] = data['strike1']
        df['signal'] = [data['signal0']] + ([data['signal1']] * (len(df) - 1))
        df = df[[
            'stock', 'dte0f', 'dte0b', 'strike0', 'strike1', 'signal',
            'option0f', 'option1f', 'option0b', 'option1b'
        ]]
        df = df.rename(columns={
            'dte0f': 'dte0', 'dte0b': 'dte1'
        })
        df.dropna(inplace=True)

        df['close'] = df['option0f'] + df['option1f'] + df['option0b'] + df['option1b']
        df['pos_net'] = [0] + list(-df['close'][1:] - df['close'].iloc[0])
        df['pos_chg'] = df['pos_net'] / np.abs(df['close'].iloc[0])
        df['pct_chg'] = df['pos_chg'] / np.abs(df['pos_chg'].shift(1))
        df = df.replace([np.inf, -np.inf], np.nan)

        # today iv
        df = df.reset_index()
        df['dte_iv'] = df.apply(
            lambda x: today_iv(df_iv, x['date'], x['dte0']),
            axis=1
        )

        # chance
        df['strike0%'] = norm.cdf(df['strike0'], df['stock'], df['dte_iv'])
        df['strike0%'] = df.apply(correct_prob, args=('strike0',), axis=1)
        df['strike1%'] = norm.cdf(df['strike1'], df['stock'], df['dte_iv'])
        df['strike1%'] = df.apply(correct_prob, args=('strike1',), axis=1)

        df = df.round({
            'close': 2,
            'pos_net': 2,
            'pos_chg': 2,
            'pct_chg': 4,
            'dte_iv': 2,
            'strike0%': 2,
            'strike1%': 2
        })

        df = df.fillna(0)

        # add into list
        df_list.append(df)

        # print df.to_string(line_width=1000)

    return df_list
