import numpy as np
import pandas as pd


def get_option(df_name, df_option, signal, min_dte, moneyness, cycle, strike):
    # day option
    try:
        df_chain = df_option.ix[signal['date0']].query('dte >= %r' % min_dte)
        df_chain = df_chain.reset_index()
    except KeyError:
        return None, None  # pass if date not found in df_option

    # call only
    df_chain = pd.merge(df_name, df_chain, on='option_code').sort('strike')
    # print df_chain.to_string(line_width=500)

    # moneyness
    if moneyness == 'OTM':
        df_chain = df_chain[df_chain['intrinsic'] == 0]
    elif moneyness == 'ITM':
        df_chain = df_chain[df_chain['intrinsic']]
    else:
        raise ValueError('Invalid moneyness value')

    #print df_chain.to_string(line_width=500)
    # cycle strike

    try:
        dte = df_chain['dte'].unique()[cycle]
        stk = df_chain[df_chain['dte'] == dte]['strike'].unique()[strike]
        option0 = df_chain.query('dte == %r & strike == %r' % (dte, stk)).iloc[0]
        #print option0
    except IndexError:
        return None, None  # cycle not exists
    #break

    # option1
    try:
        option1 = df_option.ix[signal['date1']].query(
            'option_code == %r' % option0['option_code']
        ).reset_index().loc[0]
    except (KeyError, IndexError):
        return None, None  # if not exist, skip, got fill missing

    # expire is correct
    return option0, option1


def create_order(df_stock, df_signal, df_contract, df_option,
                 moneyness=('ATM', 'OTM'), cycle=0, strike=0):
    """
    Make trade order long call strategy using cycle and strike
    :param df_stock: DataFrame
    :param df_signal: DataFrame
    :param df_contract: DataFrame
    :param df_option: DataFrame
    :param moneyness: str ('ATM', 'OTM')
    :param cycle: int
    :param strike: int
    :return: DataFrame
    """
    symbol = df_stock['symbol'][0]
    df_call = df_contract[df_contract['name'] == 'CALL']

    #for i in df_option.index.unique():
    #    print i
    data = []
    for _, signal in df_signal.iterrows():
        min_dte = (signal['date1'] - signal['date0']).days

        option0, option1 = get_option(df_call, df_option, signal, min_dte, moneyness, cycle, strike)

        try:
            #print option0['option_code'], option0['date'], option1['date']
            data.append({
                'date0': option0['date'],
                'date1': option1['date'],
                'signal0': 'BUY',
                'signal1': 'SELL',
                'stock0': float(signal['close0']),
                'stock1': float(signal['close1']),
                'close0': round(option0['ask'], 2),  # buy using ask
                'close1': round(option1['bid'], 2),  # sell using bid
                'option_code': option0['option_code'],
                'strike': option0['strike'],
                'dte0': option0['dte'],
                'dte1': option1['dte']
            })
        except TypeError:
            print signal['date0'].strftime('%Y-%m-%d'), 'missing'

    df = pd.DataFrame()
    if len(data):
        df = pd.DataFrame(data, index=range(len(data)), columns=[
            'date0', 'date1', 'signal0', 'signal1',
            'stock0', 'stock1', 'close0', 'close1',
            'option_code', 'strike', 'dte0', 'dte1',
            'intrinsic0', 'intrinsic1'
        ])

        df['holding'] = df['date1'] - df['date0']
        df['pct_chg'] = np.round((df['close1'] - df['close0']) / df['close0'], 2)

        f = lambda x: np.round(x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg'], 2)
        df['pct_chg'] = df.apply(f, axis=1)

        df['sqm0'] = 0
        df['sqm1'] = 0
        df['oqm0'] = 1
        df['oqm1'] = -1

    return df
