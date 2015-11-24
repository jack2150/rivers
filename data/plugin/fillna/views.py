from django.shortcuts import render
import numpy as np
import pandas as pd

from data.plugin.clean.clean2 import CleanOption2, extract_code
from rivers.settings import QUOTE


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
    df_contract = db.select('option/%s/contract' % symbol.lower())
    df_option = db.select('option/%s/clean' % symbol.lower()).sort_index()
    df_option = df_option.reset_index().sort_values('date')
    db.close()

    #df_option = df_option.query('option_code == "AIG110421C25"')
    #print df_option.query('option_code == "AIG110421C25"').to_string(line_width=1000)

    df_missing = df_contract.query("missing > 0 & others == ''")

    split = df_missing['right'].apply(lambda x: '/' in x)
    df_split = df_missing[split]  # split contract
    df_normal = df_missing[split == 0]  # normal contract
    df_normal = df_normal.query('missing == 1')  # testing
    # print df_normal.query('option_code == %r' % 'AIG100417C24').to_string(line_width=1000)
    df_all = pd.merge(df_option, df_normal, how='right', on=['option_code']).sort_values(
        ['option_code', 'date']
    )
    # print df_all.query('option_code == %r' % 'AIG100417C24').to_string(line_width=1000)
    # print df_split.to_string(line_width=1000)
    # print df_normal.to_string(line_width=1000)

    # todo: missing is wrong, maybe add holidays
    # print df_normal['missing']
    # print trading_dates
    new = []
    for _, data in df_normal.iterrows():
        # todo: missing 03-08-2010
        print data['option_code'], data['missing'],
        df_current = df_all.query('option_code == %r' % data['option_code']).sort_values('date')
        current_dates = list(df_current['date'])
        #print df_current.to_string(line_width=1000)

        start = df_current['date'].iloc[0]
        stop = df_current['date'].iloc[-1]
        bdays = [d for d in df_stock.index if start <= d <= stop]
        missing_dates = [d for d in bdays if d not in current_dates]

        if len(bdays) == len(current_dates):
            raise ValueError('Empty missing date: %d, %d' % (len(bdays), len(current_dates)))

        # todo: wrong missing date, fix it

        for date in missing_dates:
            print date
            loc = bdays.index(date)

            keys = []
            for i in [i for i in range(-3, 4) if i]:
                j = loc + i
                if -1 < j < len(current_dates):
                    keys.append(j)

            options = []
            for k in keys:
                options.append(
                    df_current[df_current['date'] == current_dates[k]].iloc[0]
                )

            if len(options):
                mean = {
                    'bid': np.mean([1 - (o['bid'] / o['theo_price']) for o in options]),
                    'ask': np.mean([(o['ask'] / o['theo_price']) - 1 for o in options]),
                    'impl_vol': np.mean([o['impl_vol'] for o in options if o['impl_vol']]),
                }


                for key in ('bid', 'ask', 'impl_vol'):
                    mean[key] = round(mean[key], 2)
                    mean[key] = 0.0 if np.isnan(mean[key]) or np.isinf(mean[key]) else mean[key]

                print mean

                # todo: wrong bid and ask got inf
            else:
                continue

            ex_date, name, strike = extract_code(data['option_code'])

            clean = CleanOption2(
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

            new.append({
                'date': date,
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
            })

        print ''

    df_fillna = pd.DataFrame(new)
    for key in ('prob_itm', 'prob_otm', 'prob_touch', 'impl_vol'):
        df_fillna[key] = np.round(df_fillna[key], 2)

    print df_fillna.to_string(line_width=1000)

    template = 'data/fillna_option.html'

    parameters = dict(
        site_title='Fill missing option data',
        title='Fill missing option data: %s' % symbol.upper(),
        symbol=symbol.upper(),
    )

    return render(request, template, parameters)

# todo: a lot duplicate date option, check
# todo: prob touch is wrong???