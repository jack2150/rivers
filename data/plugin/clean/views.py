import time
from django.shortcuts import render
from data.plugin.clean.clean import *
from rivers.settings import QUOTE
from numba import jit
from multiprocessing import Process, Queue


# change dtype
def mass_extract_codes(option_codes):
    """
    Extract ex_date, option and strike from a list of option code 
    :param option_codes: str
    :return: list(str, float, float)
    """
    a = ['' for _ in range(len(option_codes))]
    b = np.zeros(len(option_codes))
    c = np.zeros(len(option_codes))
    for i in range(len(option_codes)):
        a[i], b[i], c[i] = extract_code(option_codes[i])
    return a, b, c


@jit
def run_clean(ex_date, name, strike, today,
              rf_rate, close, bid, ask, impl_vol, div):
    """
    Run a single clean loop for current list of data
    :param ex_date: np.array(str)
    :param name: np.array(int)
    :param strike: np.array(float)
    :param today: np.array(str)
    :param rf_rate: np.array(float)
    :param close: np.array(float)
    :param bid: np.array(float)
    :param ask: np.array(float)
    :param impl_vol: np.array(float)
    :param div: np.array(float)
    :return: np.darray(
        float, float, float, float, float, float, float, float, float, float, float, float
    )
    """
    r = np.zeros([len(ex_date), 12], dtype='float64')
    for i in range(len(ex_date)):
        if not ex_date[i]:
            continue

        if today[i] >= ex_date[i]:
            continue

        c = CleanOption(
            ex_date[i], name[i], strike[i], today[i], rf_rate[i],
            close[i], bid[i], ask[i], impl_vol[i], div[i]
        )
        r[i][0] = round(c.impl_vol() * 100.0, 2)
        r[i][1] = c.theo_price()
        r[i][2], r[i][3] = c.moneyness()
        r[i][4] = c.dte()
        r[i][5], r[i][6], r[i][7] = c.prob()
        r[i][8], r[i][9], r[i][10], r[i][11] = c.greek()

    return r


def queue_cleaning(q, start, stop, ex_date, name, strike, today,
                   rf_rate, close, bid, ask, impl_vol, div):
    """
    Run a queue clean option process
    :param q: Queue
    :param start: int
    :param stop: int
    :param ex_date: list(str)
    :param name: list(int)
    :param strike: list(float)
    :param today: list(str)
    :param rf_rate: list(float)
    :param close: list(float)
    :param bid: list(float)
    :param ask: list(float)
    :param impl_vol: list(float)
    :param div: list(float)
    """
    q.put([start, stop, run_clean(
        ex_date, name, strike, today, rf_rate, close, bid, ask, impl_vol, div
    )])


def clean_option(request, symbol, core=6):
    """
    Cleaning option using multi process method
    multi thread is useless in heavy calculation process
    :param core: int
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
    df_contract0 = db.select('option/%s/raw/contract' % symbol.lower())
    df_option = db.select('option/%s/raw/data' % symbol.lower())
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

    # skip others and split right
    print output % ('', 'skip others and split', '')
    df_contract1 = df_contract0.query('others == "" & right == "100" & special != "Mini"')
    print output % ('', 'special: %s' % df_contract1['special'].unique(), '')
    print output % ('', 'no others: %s' % df_contract0.query('others != ""')['others'].unique(), '')
    print output % ('', 'no right: %s' % df_contract0.query('right != "100"')['right'].unique(), '')

    # time output
    t1 = time.time()
    print output % (1, 'start merging', '%10d secs' % (t1 - t0))
    t0 = t1

    # merge all into a single table
    df_skip = pd.merge(
        df_option,
        df_contract0.query('others != "" | right != "100" | special == "Mini"'),
        how='inner', on='option_code'
    )
    df_all = pd.merge(df_option, df_contract1, how='inner', on='option_code').sort_values(
        ['option_code', 'date']
    )
    df_all = pd.merge(df_all, df_stock.reset_index(), how='inner', on=['date'])
    df_all = pd.merge(df_all, df_rate.reset_index(), how='inner', on=['date'])
    df_all = pd.merge(df_all, df_div.reset_index(), how='inner', on=['date'])
    df_all = df_all.reset_index()
    del df_all['index']

    total = len(df_all)
    print output % ('', 'total length df_option', '%10d rows' % len(df_option))
    print output % ('', 'total length df_contract0', '%10d rows' % len(df_contract0))
    print output % ('', 'total length df_contract1', '%10d rows' % len(df_contract1))
    print output % ('', 'total length df_skip', '%10d rows' % len(df_skip))
    print output % ('', 'total length df_all', '%10d rows' % len(df_all))

    if len(df_all) + len(df_skip) != len(df_option):
        raise ValueError('Invalid merging data rows!')

    t1 = time.time()
    print output % (2, 'start cleaning', '%10d secs' % (t1 - t0))
    t0 = t1

    # multi process cleaning
    q = Queue()
    p = []
    n = core
    m = int(total / float(n))
    l = range(0, total, m)
    l[-1] = total
    print output % ('3', 'process steps %s' % l, '')
    for start, stop in zip(l[:-1], l[1:]):
        df = df_all[start:stop].reset_index()

        ex_date, name, strike = mass_extract_codes(df['option_code'])
        df['date2'] = df['date'].apply(lambda d: d.date().strftime('%y%m%d'))

        p.append(Process(target=queue_cleaning, args=(
            q, start, stop,
            ex_date, name, strike, df['date2'],
            df['rate'], df['close'], df['bid'], df['ask'],
            df['impl_vol'], df['div']
        )))

        print output % ('', 'processing created', '%10d [%d, %d]' % (len(p) - 1, start, stop))

    for i in range(len(p)):
        print output % ('', 'processing started', '%10d' % i)
        p[i].start()

    df_result = pd.DataFrame()
    for i in range(len(p)):
        start, stop, df = q.get()

        if len(df_result):
            df_result = pd.concat([df_result, pd.DataFrame(df, index=range(start, stop))])
        else:
            df_result = pd.DataFrame(df, index=range(start, stop))

    for i in range(len(p)):
        print output % ('', 'processing closed', '%10d' % i)
        p[i].join()

    t1 = time.time()
    print output % (4, 'start updating', '%10d secs' % (t1 - t0))
    t0 = t1

    # update
    df_result = df_result.sort_index()
    df_result.columns = [
        'impl_vol', 'theo_price', 'intrinsic', 'extrinsic',
        'dte', 'prob_itm', 'prob_otm', 'prob_touch',
        'delta', 'gamma', 'theta', 'vega'
    ]
    df_clean = df_all[['date', 'ask', 'bid', 'last', 'mark', 'open_int', 'option_code', 'volume']]
    df_clean = pd.concat([df_clean, df_result], axis=1)
    """:type: pd.DataFrame"""

    t1 = time.time()
    print output % (5, 'save data', '%10d secs' % (t1 - t0))
    t0 = t1

    # remove all
    df_clean = df_clean.set_index('date')

    if len(df_clean) != total:
        raise ValueError('Invalid clean option: (%d, %d)' % (total, len(df_clean)))

    db = pd.HDFStore(QUOTE)
    for key in ('contract', 'data'):
        try:
            db.remove('option/%s/clean/%s' % (symbol.lower(), key))
        except KeyError:
            pass
    db.append('option/%s/clean/contract' % symbol.lower(), df_contract1,
              format='table', data_columns=True, min_itemsize=100)
    db.append('option/%s/clean/data' % symbol.lower(), df_clean,
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
