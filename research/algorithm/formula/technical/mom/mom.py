"""
Type: Technical Analysis
Name: Momentum rule
Method: Change of momentum
"""
import numpy as np


def handle_data(df, period_span=0, skip_days=0, holding_period=0):
    if period_span < 0:
        raise ValueError('Invalid period_span, lower than zero: %d' % period_span)

    if skip_days < 0:
        raise ValueError('Invalid skip_days, lower than zero: %d' % period_span)

    if holding_period < 0:
        raise ValueError('Invalid holding_period, lower than zero: %d' % period_span)

    # mom rule using period span days
    df['x_close'] = df['close'].shift(-period_span)
    df['x_date'] = df['date'].shift(-period_span)
    df['net_chg'] = df['x_close'] - df['close']
    df['signal'] = df['net_chg'].apply(
        lambda x: 'BUY' if x > 0 else ('SELL' if x < 0 else np.nan)
    )

    # print df.to_string(line_width=1000)

    # wait x days before enter
    df['dateEnter'] = df['x_date'].shift(-skip_days)
    df['closeEnter'] = df['x_close'].shift(-skip_days)

    # after enter hold for x days (after 5 days wait, holding 60 days = 65 days)
    df['dateExit'] = df['x_date'].shift(-(holding_period + skip_days))
    df['closeExit'] = df['x_close'].shift(-(holding_period + skip_days))

    return df.copy()


def create_signal(df, direction=('follow', 'long', 'short'),
                  side=('follow', 'reverse', 'buy', 'sell')):
    if direction not in ('follow', 'long', 'short'):
        raise ValueError('Invalid direction value')

    if side not in ('follow', 'reverse', 'buy', 'sell'):
        raise ValueError('Invalid side value')

    df2 = df[df['signal'] != df['signal'].shift(1)].dropna()
    # print df2.to_string(line_width=1000)

    df2['date0'] = df2['x_date']
    df2['close0'] = df2['x_close']
    df2['signal0'] = df2['signal']
    df2['date1'] = df2['x_date'].shift(-1)
    df2['close1'] = df2['x_close'].shift(-1)
    df2['signal1'] = df2['signal'].shift(-1)
    # print df2.to_string(line_width=1000)

    df2 = df2[[
        'date0', 'date1', 'signal0', 'signal1', 'close0', 'close1',
        'dateEnter', 'closeEnter', 'dateExit', 'closeExit'
    ]]
    # print df2.to_string(line_width=1000)

    # set enter, date and close
    df2['close0'] = df2.apply(
        lambda x: x['closeEnter'] if x['date0'] < x['dateEnter'] else x['close0'],
        axis=1
    )
    df2['date0'] = df2.apply(
        lambda x: x['dateEnter'] if x['date0'] < x['dateEnter'] else x['date0'],
        axis=1
    )

    # drop date0 < date1 where less than x days holding period
    df2 = df2[df2['date0'] < df2['date1']]
    # print df2.to_string(line_width=1000)

    # set exit, date and close
    df2['close1'] = df2.apply(
        lambda x: x['close1'] if x['date0'] == x['dateExit'] else x['closeExit'],
        axis=1
    )
    df2['date1'] = df2.apply(
        lambda x: x['date1'] if x['date0'] == x['dateExit'] else x['dateExit'],
        axis=1
    )

    # reset column
    df2 = df2[['date0', 'date1', 'signal0', 'signal1', 'close0', 'close1']]

    # direction: buy or sell
    if direction == 'long':
        df2 = df2[df2['signal0'] == 'BUY']
    elif direction == 'short':
        df2 = df2[df2['signal0'] == 'SELL']

    # side: buy or sell
    if side == 'buy':
        df2['signal0'] = 'BUY'
        df2['signal1'] = 'SELL'
    elif side == 'sell':
        df2['signal0'] = 'SELL'
        df2['signal1'] = 'BUY'
    elif side == 'reverse':
        df2['signal0'] = df2['signal0'].apply(lambda x: 'SELL' if x == 'BUY' else 'BUY')
        df2['signal1'] = df2['signal1'].apply(lambda x: 'BUY' if x == 'SELL' else 'SELL')

    df2['holding'] = df2['date1'] - df2['date0']
    df2['pct_chg'] = (df2['close1'] - df2['close0']) / df2['close0']

    # apply algorithm result
    df2['pct_chg'] = df2.apply(
        lambda x: x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg'],
        axis=1
    )

    df2 = df2.round({
        'pct_chg': 4
    })
    df2.reset_index(drop=True, inplace=True)

    return df2.copy()
