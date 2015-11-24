import time
from django.shortcuts import render
import numpy as np
import pandas as pd
from data.plugin.clean.clean2 import CleanOption2, get_div_yield, extract_code
from rivers.settings import QUOTE
from numba import jit
from multiprocessing import Process, Queue


# change dtype
def ex_code(code):
    a = ['' for _ in range(len(code))]
    b = np.zeros(len(code))
    c = np.zeros(len(code))
    for i in range(len(code)):
        a[i], b[i], c[i] = extract_code(code[i])
    return a, b, c


@jit
def clean(ex_date, name, strike, today, rf_rate, close, bid, ask, impl_vol, div):
    r = np.zeros([len(ex_date), 12], dtype='float32')
    for i in range(len(ex_date)):
        if not ex_date[i]:
            continue

        if today[i] >= ex_date[i]:
            continue

        c = CleanOption2(
            ex_date[i], name[i], strike[i], today[i], rf_rate[i],
            close[i], bid[i], ask[i], impl_vol[i], div[i]
        )
        r[i][0] = c.impl_vol()
        r[i][1] = c.theo_price()
        r[i][2], r[i][3] = c.moneyness()
        r[i][4] = c.dte()
        r[i][5], r[i][6], r[i][7] = c.prob()
        r[i][8], r[i][9], r[i][10], r[i][11] = c.greek()

    return r


def clean2(q, start, stop, ex_date, name, strike, today, rf_rate, close, bid, ask, impl_vol, div):
    q.put([start, stop, clean(ex_date, name, strike, today, rf_rate, close, bid, ask, impl_vol, div)])


@jit
def fill_zero(old, new):
    r = np.zeros(len(old))
    for i in range(len(old)):
        if old[i]:
            r[i] = old[i]
        else:
            r[i] = new[i]

    return r


@jit
def moneyness(old, new):
    r = np.zeros(len(old))
    for i in range(len(old)):
        if old[i] <= 0:
            r[i] = new[i]
        else:
            r[i] = old[i]

    return r


@jit
def dte(old, new):
    r = np.zeros(len(old))
    for i in range(len(old)):
        if old[i] != new[i]:
            r[i] = new[i]
        else:
            r[i] = old[i]

    return r


@jit
def prob(name, itm, otm, touch, new):
    r = np.zeros(len(new))
    old = {
        'prob_itm': itm,
        'prob_otm': otm,
        'prob_touch': touch,
    }[name]

    for i in range(len(new)):
        r[i] = old[i]

        if itm[i] == 100 or otm[i] == 100 or itm[i] == 0 or otm[i] == 0:
            r[i] = new[i]

    return r


@jit
def greek(name, delta, gamma, theta, vega, new):
    r = np.zeros(len(new))
    old = {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega,
    }[name]

    for i in range(len(new)):
        if delta[i] or gamma[i] or theta[i] or vega[i]:
            r[i] = old[i]
        else:
            r[i] = new[i]

    return r


def clean_option3(request, symbol):
    """

    :param request: request
    :param symbol: str
    :return: render
    """
    output = '%-3s %-30s %-s'
    print output % (0, 'load data', '')
    t0 = time.time()
    db = pd.HDFStore(QUOTE)
    df_rate = db.select('treasury/RIFLGFCY01_N_B')  # series
    df_stock = db.select('stock/thinkback/%s' % symbol.lower())
    df_stock = df_stock[['close']]
    df_contract = db.select('option/%s/contract' % symbol.lower())
    df_option = db.select('option/%s/raw' % symbol.lower())
    df_option = df_option.reset_index()
    try:
        df_dividend = db.select('event/dividend/%s' % symbol.lower())
        df_div = get_div_yield(df_stock, df_dividend)
    except KeyError:
        df_div = pd.DataFrame()
        df_div['date'] = df_stock.index
        df_div['amount'] = 0.0
        df_div['div'] = 0.0
    db.close()

    # df_option = df_option[df_option['option_code'] == 'AIG100417C24']
    # print df_option.to_string(line_width=1000)

    # todo: skip others, skip special

    t1 = time.time()
    print output % (1, 'start merging', '%10d secs' % (t1 - t0))
    t0 = t1

    # merge all into a single table
    df_all = pd.merge(df_option, df_contract, how='inner', on='option_code').sort_values(
        ['option_code', 'date']
    )
    df_all = pd.merge(df_all, df_stock.reset_index(), how='inner', on=['date'])
    df_all = pd.merge(df_all, df_rate.reset_index(), how='inner', on=['date'])
    df_all = pd.merge(df_all, df_div.reset_index(), how='inner', on=['date'])

    total = len(df_all)
    print output % ('1a', 'total length df_all', '%10d rows' % total)
    print output % ('1b', 'total length df_contract', '%10d rows' % len(df_contract))
    if len(df_all) != len(df_option):
        raise ValueError('Invalid merging data rows!')

    t1 = time.time()
    print output % (2, 'start cleaning', '%10d secs' % (t1 - t0))
    t0 = t1

    # multi process cleaning
    q = Queue()
    p = []
    n = 6
    m = int(total / float(n))
    l = range(0, total, m)
    l[-1] = total
    print output % ('3a', 'process steps %s' % l, '')
    for start, stop in zip(l[:-1], l[1:]):
        df = df_all[start:stop].reset_index()

        ex_date, name, strike = ex_code(df['option_code'])
        df['date2'] = df['date'].apply(lambda d: d.date().strftime('%y%m%d'))

        p.append(Process(target=clean2, args=(
            q, start, stop,
            ex_date, name, strike, df['date2'],
            df['rate'], df['close'], df['bid'], df['ask'],
            df['impl_vol'], df['div']
        )))

        print output % ('3b', 'processing created', '%10d [%d, %d]' % (len(p) - 1, start, stop))

    for i in range(len(p)):
        print output % ('3c', 'processing started', '%10d' % i)
        p[i].start()

    df_result = pd.DataFrame()
    for i in range(len(p)):
        start, stop, df = q.get()

        if len(df_result):
            df_result = pd.concat([df_result, pd.DataFrame(df, index=range(start, stop))])
        else:
            df_result = pd.DataFrame(df, index=range(start, stop))

    for i in range(len(p)):
        print output % ('3c', 'processing closed', '%10d' % i)
        p[i].join()

    t1 = time.time()
    print output % (4, 'start updating', '%10d secs' % (t1 - t0))
    t0 = t1

    # update
    df_result = df_result.sort_index()
    df_result.columns = [
        'impl_vol2', 'theo_price2', 'intrinsic2', 'extrinsic2', 'dte2',
        'prob_itm_2', 'prob_otm_2', 'prob_touch_2',
        'delta_2', 'gamma_2', 'theta_2', 'vega_2'
    ]
    df_clean = pd.concat([df_all, df_result], axis=1)
    """:type: pd.DataFrame"""

    # clean data using result
    df_clean['impl_vol'] = np.round(fill_zero(df_clean['impl_vol'], df_clean['impl_vol2'] * 100), 2)
    df_clean['theo_price'] = np.round(fill_zero(df_clean['theo_price'], df_clean['theo_price2']), 2)
    df_clean['intrinsic'] = moneyness(df_clean['intrinsic'], df_clean['intrinsic2'])
    df_clean['extrinsic'] = moneyness(df_clean['extrinsic'], df_clean['extrinsic2'])
    df_clean['dte'] = dte(df_clean['dte'], df_clean['dte2'])
    i = {}
    for x in ('prob_itm', 'prob_otm', 'prob_touch'):
        i[x] = prob(
            x,
            df_clean['prob_itm'], df_clean['prob_otm'], df_clean['prob_touch'],
            df_clean['%s_2' % x]
        )
    for x in ('prob_itm', 'prob_otm', 'prob_touch'):
        df_clean[x] = np.around(i[x], 2)

    i = {}
    for x in ('delta', 'gamma', 'theta', 'vega'):
        i[x] = greek(
            x,
            df_clean['delta'], df_clean['gamma'], df_clean['theta'], df_clean['vega'],
            df_clean['%s_2' % x]
        )
    for x in ('delta', 'gamma', 'theta', 'vega'):
        df_clean[x] = np.around(i[x], 2)

    t1 = time.time()
    print output % (5, 'save data', '%10d secs' % (t1 - t0))
    t0 = t1

    # remove all
    df_clean = df_clean[[
        'date', 'ask', 'bid', 'delta', 'dte', 'extrinsic', 'gamma', 'impl_vol',
        'intrinsic', 'last', 'mark', 'open_int', 'option_code', 'prob_itm', 'prob_otm',
        'prob_touch', 'theo_price', 'theta', 'vega', 'volume'
    ]]
    df_clean = df_clean.set_index('date')

    if len(df_clean) != total:
        raise ValueError('Invalid clean option: (%d, %d)' % (total, len(df_clean)))

    db = pd.HDFStore(QUOTE)
    try:
        db.remove('option/%s/clean' % symbol.lower())
    except KeyError:
        pass
    db.append('option/%s/clean' % symbol.lower(), df_clean,
              format='table', data_columns=True)
    db.close()

    t1 = time.time()
    print output % (6, 'exit', '%10d secs' % (t1 - t0))

    template = 'data/clean_option.html'
    parameters = dict(
        site_title='Clean option data',
        title='Clean option data: %s' % symbol.upper(),
        symbol=symbol.upper(),
    )

    return render(request, template, parameters)
