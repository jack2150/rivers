from data.plugin.clean.clean import CleanOption, extract_code
from django.shortcuts import render
import numpy as np
import pandas as pd
from rivers.settings import QUOTE


output = '%-6s | %-30s %s'


def fillna_option(request, symbol):
    """
    Fill missing option data
    :param request: request
    :param symbol: str
    :return: render
    """
    db = pd.HDFStore(QUOTE)
    df_rate = db.select('treasury/RIFLGFCY01_N_B')  # series
    df_rate = df_rate['rate']
    df_stock = db.select('stock/thinkback/%s' % symbol.lower())
    df_stock = df_stock['close']
    df_contract = db.select('option/%s/clean/contract' % symbol.lower())
    df_clean = db.select('option/%s/clean/data' % symbol.lower())
    df_clean = df_clean.reset_index().sort_values('date')
    db.close()

    df_missing = df_contract.query("missing > 0")
    df_all = pd.merge(df_clean, df_missing, how='right', on=['option_code']).sort_values(
        ['option_code', 'date']
    )

    stock_days = pd.Series(df_stock.index)

    # df_all = df_all.query('option_code == %r' % 'AIG150501P75')

    new = []
    for _, c in df_missing.iterrows():
        # todo: % of missing date
        df_current = df_all.query('option_code == %r' % c['option_code']).sort_values('date')

        if len(df_current) == 0:
            continue

        print output % ('CODE', 'Total missing: %d, total option: %d' % (
            c['missing'], len(df_current)
        ), c['option_code'])

        current_dates = df_current['date']
        # print df_current.to_string(line_width=1000)

        start = df_current['date'].iloc[0]
        stop = c['ex_date']
        bdays = stock_days[(start <= stock_days) & (stock_days <= stop)]
        mdays = bdays[~bdays.isin(current_dates)]

        if c['missing'] / float(len(bdays) + len(mdays)) > 0.25:
            print output % (
                'SKIP', 'Too many missing:', '%.2f%%' % (c['missing'] / float(len(bdays)) * 100)
            )
            continue

        if len(current_dates) < 2:
            print output % (
                'SKIP', 'Less than 4 rows:', 'total: %d' % len(current_dates)
            )
            continue

        if len(bdays) == len(current_dates):
            raise ValueError('Empty missing date, stock day: %d, option days %d' % (
                len(bdays), len(current_dates)
            ))

        for date in mdays:
            print output % (
                'MISS', 'CODE: %s' % c['option_code'], 'DATE: %s' % date.strftime('%Y-%m-%d')
            )

            i = bdays[bdays == date].index[0]
            df_date = df_current[df_current['date'].isin(bdays[range(i - 3, i + 4)])]
            df_date = df_date[df_date['impl_vol'] > 0]  # if not result inf

            if len(df_date):
                # noinspection PyUnresolvedReferences
                mean = {
                    'bid': round((1 - (df_date['bid'] / df_date['theo_price'])).mean(), 2),
                    'ask': round(((df_date['ask'] / df_date['theo_price']) - 1).mean(), 2),
                    'impl_vol': round(df_date['impl_vol'].mean(), 2),
                }
                print output % ('DATA', 'Use nearby data', 'total: %d' % len(df_date))
                print output % ('', mean, '')
            else:
                print output % ('SKIP', 'No nearby date exist', '')
                continue

            ex_date, name, strike = extract_code(c['option_code'])

            clean = CleanOption(
                ex_date,
                name,
                strike,
                date.strftime('%y%m%d'),
                round(df_rate[date], 4),
                round(df_stock[date], 4),
                0.0,
                0.0,
                mean['impl_vol'],
                0.0  # later
            )

            theo_price = clean.theo_price()
            bid = round(theo_price * (1 - mean['bid']), 2)
            ask = round(theo_price * (1 + mean['ask']), 2)
            clean.bid = bid
            clean.ask = ask
            intrinsic, extrinsic = clean.moneyness()
            dte = clean.dte()
            prob_itm, prob_otm, prob_touch = clean.prob()
            delta, gamma, theta, vega = clean.greek()

            # todo: open interest and volume use nearest

            print output % (
                'FILL', 'bid: %.2f, ask: %.2f' % (bid, ask),
                'Date: %s' % date.strftime('%Y-%m-%d'),
            )

            data = {
                'date': date,
                # 'close': round(df_stock[date], 2),
                'option_code': c['option_code'],
                'impl_vol': mean['impl_vol'],
                'theo_price': theo_price,
                'bid': bid,
                'ask': ask,
                'intrinsic': intrinsic + 0,
                'extrinsic': extrinsic + 0,
                'dte': dte,
                'prob_itm': prob_itm,
                'prob_otm': prob_otm,
                'prob_touch': prob_touch,
                'delta': delta,
                'gamma': gamma,
                'theta': theta,
                'vega': vega,
                'last': 0.0,
                'mark': round((bid + ask) / 2.0, 2),
                'open_int': 0.0,
                'volume': 0.0,
            }

            new.append(data)

            # update df_all
            df_current = pd.concat([df_current, pd.DataFrame([data])])

    if len(new):
        # make df
        df_fillna = pd.DataFrame(new)
        for key in ('prob_itm', 'prob_otm', 'prob_touch', 'impl_vol'):
            df_fillna[key] = np.round(df_fillna[key], 2)
        # print df_fillna.to_string(line_width=1000)

        # merge clean and fillna
        df_new = pd.concat([df_clean, df_fillna])
        """:type: pd.DataFrame"""
        df_new = df_new.reset_index(drop=True)

        # update missing
        print output % ('MISS', 'Update contract missing count', '')
        counts = df_fillna['option_code'].value_counts()
        for key, value in zip(counts.index, counts.values):
            df_contract.loc[df_contract['option_code'] == key, 'missing'] -= value

        # set date as index before save
        df_new = df_new.set_index('date')
        print df_new.tail().to_string(line_width=1000)

        # save into clean
        print output % ('SAVE', 'Remove and insert with fillna data', '')
        db = pd.HDFStore(QUOTE)
        for key in ('contract', 'data'):
            try:
                db.remove('option/%s/clean/%s' % (symbol.lower(), key))
            except KeyError:
                pass
        db.append('option/%s/clean/contract' % symbol.lower(), df_contract,
                  format='table', data_columns=True, min_itemsize=100)
        db.append('option/%s/clean/data' % symbol.lower(), df_new,
                  format='table', data_columns=True, min_itemsize=100)
        db.close()

    # template
    template = 'data/fillna_option.html'

    parameters = dict(
        site_title='Fill missing option data',
        title='Fill missing option data: %s' % symbol.upper(),
        symbol=symbol.upper(),
    )

    return render(request, template, parameters)
