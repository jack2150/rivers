from simulation.strategy.single.single import *


def create_order(df_stock, df_signal, moneyness=('OTM', 'ITM'),
                 cycle=0, strike=0, expire=(False, True)):
    """
    Create protective put strategy using,
    BUY stock BUY option (ask) -> SELL stock SELL option (bid)
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
                stock0 = tb_closes[option0.date.strftime('%Y-%m-%d')]
                close0 = stock0 + np.float(option0.ask)

                bid1 = 0
                if expire:
                    bid1 = np.float(
                        np.float(option0.contract.strike)
                        - tb_closes[option1.date.strftime('%Y-%m-%d')]
                    )
                    bid1 = bid1 if bid1 > 0 else 0.0

                    date1 = option1.date
                    stock1 = tb_closes[option1.date.strftime('%Y-%m-%d')]
                    close1 = stock1 + np.float(bid1)
                else:
                    date1 = option1.date
                    stock1 = tb_closes[option1.date.strftime('%Y-%m-%d')]
                    close1 = stock1 + np.float(option1.bid)

                data.append({
                    'date0': option0.date,
                    'date1': date1,
                    'signal0': 'BUY',
                    'signal1': 'SELL',
                    'stock0': stock0,
                    'stock1': stock1,
                    'option0': option0.ask,
                    'option1': bid1 if expire else option1.bid,
                    'close0': np.round(close0, 2),  # buy using ask
                    'close1': np.round(close1, 2),  # sell using bid
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
            'stock0', 'stock1', 'option0', 'option1', 'close0', 'close1',
            'option_code', 'strike', 'dte0', 'dte1',
            'intrinsic0', 'intrinsic1'
        ])

        df['holding'] = df['date1'] - df['date0']
        df['pct_chg'] = np.round((df['close1'] - df['close0']) / df['close0'], 2)

        f = lambda x: np.round(x['pct_chg'] * -1 if x['signal0'] == 'SELL' else x['pct_chg'], 2)
        df['pct_chg'] = df.apply(f, axis=1)

        df['sqm0'] = 100
        df['sqm1'] = -100
        df['oqm0'] = -1
        df['oqm1'] = 1

    return df
