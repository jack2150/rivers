from simulation.strategy.single.single import *


def create_order(df_stock, df_signal, moneyness=('OTM', 'ITM'),
                 cycle=0, strike=0, expire=(False, True)):
    """
    Create long put strategy using, BUY (ask), SELL (bid)
    :param df_stock: DataFrame
    :param df_signal: DataFrame
    :param moneyness: str
    :param cycle: int
    :param strike: int
    :param expire: bool
    :return: DataFrame
    """
    symbol = df_stock.ix[df_stock.index.values[0]]['symbol']

    tb_closes = {
        stock.date.strftime('%Y-%m-%d'): np.float(stock.close) for stock in
        Stock.objects.filter(Q(symbol=symbol) & Q(source='thinkback'))
    }

    holding = df_signal['holding'].apply(
        lambda x: int(x / np.timedelta64(1, 'D'))
    ).astype(np.int).min()

    data = list()
    dates0, options0 = get_options_by_cycle_strike(
        symbol=symbol,
        name='PUT',
        dates0=df_signal['date0'],
        dte=holding,
        moneyness=moneyness,
        cycle=cycle,
        strike=strike
    )

    for date0, (index, signal) in zip(dates0, df_signal.iterrows()):
        date1 = signal['date1']

        if date0:
            option0 = options0.get(date=date0)

            option1 = None
            if option0 and option0.ask > 0:
                date1, option1 = get_option_by_contract_date(option0.contract, date1)

            if option0 and option1:
                if expire:
                    close1 = np.float(
                        np.float(option0.contract.strike) -
                        tb_closes[option1.date.strftime('%Y-%m-%d')]
                    )
                    close1 = close1 if close1 > 0 else 0.0
                else:
                    date1 = option1.date
                    close1 = np.float(option1.bid)

                data.append({
                    'date0': option0.date,
                    'date1': date1,
                    'signal0': 'BUY',
                    'signal1': 'SELL',
                    'stock0': np.float(signal['close0']),
                    'stock1': np.float(signal['close1']),
                    'close0': np.float(option0.ask),  # buy using ask
                    'close1': round(np.float(close1), 2),  # sell using bid
                    'option_code': option0.contract.option_code,
                    'strike': np.float(option0.contract.strike),
                    'dte0': np.int(option0.dte),
                    'dte1': np.int(option1.dte),
                    'intrinsic0': np.float(option0.intrinsic),
                    'intrinsic1': np.float(option1.intrinsic)
                })

    df = DataFrame()
    if len(data):
        df = DataFrame(data, columns=[
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
