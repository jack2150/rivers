from data.fetch.option_cs.option_cs import *


def create_order(df_stock, df_signal, moneyness=('OTM', 'ITM', 'ATM'),
                 cycle=0, strike=0, wide=1, expire=(False, True)):
    """
    Create long call vertical strategy using, BUY (ask - bid), SELL (bid - ask)
    :param df_stock: DataFrame
    :param df_signal: DataFrame
    :param moneyness: str
    :param cycle: int
    :param strike: int
    :param expire: bool
    :return: DataFrame
    """
    if moneyness != 'ATM' and wide < 1:
        raise ValueError('Option strike wide must be greater than 0.')

    symbol = df_stock.ix[df_stock.index.values[0]]['symbol']

    tb_closes = {
        stock.date.strftime('%Y-%m-%d'): np.float(stock.close) for stock in
        Stock.objects.filter(Q(symbol=symbol) & Q(source='thinkback'))
    }

    holding = df_signal['holding'].apply(
        lambda x: int(x / np.timedelta64(1, 'D'))
    ).astype(np.int).min()

    data = list()
    if moneyness == 'ATM':
        moneyness1 = 'ITM'
        moneyness2 = 'OTM'
        strike1 = strike
        strike2 = wide
    elif moneyness == 'OTM':
        moneyness1 = moneyness
        moneyness2 = moneyness
        strike1 = strike
        strike2 = strike + wide
    elif moneyness == 'ITM':
        moneyness1 = moneyness
        moneyness2 = moneyness
        strike1 = strike + wide
        strike2 = strike
    else:
        raise ValueError('Invalid moneyness argument %s.' % moneyness)

    dates0a, options0a = get_options_by_cycle_strike(
        symbol=symbol,
        name='PUT',
        dates0=df_signal['date0'],
        dte=holding,
        moneyness=moneyness1,
        cycle=cycle,
        strike=strike1
    )
    dates0b, options0b = get_options_by_cycle_strike(
        symbol=symbol,
        name='PUT',
        dates0=df_signal['date0'],
        dte=holding,
        moneyness=moneyness2,
        cycle=cycle,
        strike=strike2
    )

    for date0a, date0b, (index, signal) in zip(dates0a, dates0b, df_signal.iterrows()):
        date1 = signal['date1']

        if date0a == date0b and date0a and date0b:
            #print date0a, date0b, date0a == date0b,
            option0a = options0a.get(date=date0a)
            option0b = options0b.get(date=date0b)

            close0 = option0a.ask - option0b.bid

            if close0 < 0.01:
                close0 = 0.0
                print '%s close0 is less than 0.01, unable to buy: %s' % (date0a, close0)

            # print signal['close0'], signal['close1']
            #print option0a.contract.strike, option0b.contract.strike
            #print option0a.ask, option0b.bid, close0

            option1a = None
            option1b = None
            close1 = 0
            if close0:
                date1a, option1a = get_option_by_contract_date(option0a.contract, date1)
                date1b, option1b = get_option_by_contract_date(option0b.contract, date1)

                if option1a and option1b:
                    if int(expire):
                        price1 = tb_closes[option1a.date.strftime('%Y-%m-%d')]
                        bid1 = np.float(np.float(option0a.contract.strike) - price1)
                        bid1 = bid1 if bid1 > 0 else 0.0
                        ask1 = np.float(np.float(option0b.contract.strike) - price1)
                        ask1 = ask1 if ask1 > 0 else 0.0
                        close1 = bid1 - ask1
                    else:
                        # when close, reverse ask bid into bid ask
                        close1 = np.float(option1a.bid - option1b.ask)

                        if close1 < 0:
                            close1 = 0.0
                else:
                    print 'No %s data: %s & %s\n\n' % (date1, option0a, option0b)

            if option0a and option0b and option1a and option1b and close0:
                data.append({
                    'date0': option0a.date,
                    'date1': date1,
                    'signal0': 'BUY',
                    'signal1': 'SELL',
                    'stock0': np.float(signal['close0']),
                    'stock1': np.float(signal['close1']),
                    'option0a': np.float(option0a.ask),
                    'option0b': np.float(option0b.bid),
                    'option1a': np.float(option1a.bid),
                    'option1b': np.float(option1b.ask),
                    'close0': np.float(close0),  # buy using ask
                    'close1': np.float(close1),  # sell using bid
                    'option_code0': option0a.contract.option_code,
                    'option_code1': option0b.contract.option_code,
                    'strike0': np.float(option0a.contract.strike),
                    'strike1': np.float(option0b.contract.strike),
                    'dte0': np.int(option0a.dte),
                    'dte1': np.int(option1a.dte)
                })

    df = DataFrame()
    if len(data):
        df = DataFrame(data, columns=[
            'date0', 'date1', 'signal0', 'signal1',
            'stock0', 'stock1',
            'option0a', 'option0b', 'option1a', 'option1b',
            'close0', 'close1',
            'option_code0', 'option_code1',
            'strike0', 'strike1', 'dte0', 'dte1',
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