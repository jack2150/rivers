import calendar
from glob import glob
import os
import re
from django.shortcuts import render
from data.extra import offday, holiday
from data.models import Underlying
from data.plugin.thinkback import ThinkBack
from rivers.settings import QUOTE, BASE_DIR
import numpy as np
import pandas as pd


def make_code(c, extra, strike, symbol):
    """
    Make new option code using contract data
    :param c: dict
    :param extra: int
    :param strike: float
    :param symbol: str
    :return: str
    """
    new_code = '{symbol}{extra}{year}{month}{day}{name}{strike}'.format(
        symbol=symbol.upper(),
        extra=extra,
        year=c['ex_date'].date().strftime('%y'),
        month=c['ex_date'].date().strftime('%m'),
        day=c['ex_date'].date().strftime('%d'),
        name=c['name'][0].upper(),
        strike=strike
    )
    return new_code


def new_code_format(symbol, c, df_contract):
    """
    Update old code format into new code
    also fix wrong symbol
    :param symbol: str
    :param c: str
    :param df_contract: DataFrame
    :return: str, str
    """
    update = False
    old_code = ''
    new_code = ''
    all_codes = list(df_contract['option_code'])

    extra = ''
    if c['special'] == 'Mini':
        extra = 7
    elif '; US$' in c['others']:
        extra = 2
    elif 'US$' in c['others']:
        extra = 1
    else:  # no others detail, so check int
        try:
            int(c['right'])  # unable convert as int mean split
        except ValueError:
            extra = 1

    if len(c['option_code']) < 6:  # exist in expire code
        strike = str(c['strike'])
        if strike[-2:] == '.0':
            strike = strike.replace('.0', '')

        new_code = make_code(c, extra, strike, symbol)

        if new_code in all_codes:
            if extra:
                while new_code in all_codes:
                    extra += 1
                    new_code = make_code(c, extra, strike, symbol)
            else:
                raise ValueError('Option code already exist in contract')
        else:
            print 'C | CODE UPDATE  | %-27s | %-14s => %-14s' % (
                'OLD UPDATE INTO NEW FORMAT', c['option_code'], new_code
            )

        update = True

    elif symbol.upper() not in c['option_code']:
        # if symbol not in option code
        old_code = c['option_code']
        if '.' in c['option_code']:
            code = re.search('^[A-Z]+(\d+[CP]+\d*[.]\d+)', c['option_code']).group(1)
        else:
            code = re.search('^[A-Z]+(\d+[CP]+\d+)', c['option_code']).group(1)

        new_code = '{symbol}{extra}{code}'.format(
            symbol=symbol.upper(), extra=extra, code=code
        )
        print 'C | CODE UPDATE  | %-27s | %-14s => %-14s' % (
            'WRONG SYMBOL', c['option_code'], new_code
        )

        update = True

    if update:
        # change old code, not new code
        count = len(df_contract.query('option_code == %r' % c['option_code']))
        if count > 1:
            print c['option_code'], count
            raise

        df_contract.loc[df_contract['option_code'] == c['option_code'], 'option_code'] = new_code

        old_code = c['option_code']

        if len(df_contract[df_contract['option_code'] == c['option_code']]):
            raise IndexError('old code %s still exists: %s' % (old_code, new_code))

    return old_code, new_code


def get_dte_date(ex_month, ex_year):
    """
    Use option contract ex_month and ex_year to get dte date
    :param ex_month: str
    :param ex_year: int
    :return: date
    """
    year = pd.datetime.strptime(str('%02d' % ex_year), '%y').year
    calendar.setfirstweekday(calendar.SUNDAY)
    month_abbr = [calendar.month_abbr[i].upper() for i in range(1, 13)]

    if len(ex_month) == 4:
        # not 3th week
        month = month_abbr.index(ex_month[:3]) + 1
        week = int(ex_month[3:])
    else:
        # standard 3th week
        month = month_abbr.index(ex_month[:3]) + 1
        week = 3

    # every week need trading day as whole
    c = calendar.monthcalendar(ex_year, month)
    for w in c:
        if not any(w[1:6]):
            del c[c.index(w)]

    # get day in calendar
    day = c[week - 1][-2]
    if day == 0:
        day = [d for d in c[week - 1] if d != 0][-1]

    return pd.Timestamp('%04d%02d%02d' % (year, month, day)).date()


def get_exist_stocks(symbol):
    """
    get symbol dataframe from quote db
    :param symbol:
    :return: DataFrame
    """
    db = pd.HDFStore(QUOTE)
    try:
        df_stock = db.select('stock/thinkback/%s' % symbol.lower())
    except KeyError:
        df_stock = pd.DataFrame({})
    db.close()

    return df_stock


def code2key(option_code):
    """
    Replace option code into hdf5 table key
    :param option_code: str
    :return: str
    """
    return str(option_code).replace('.', '_')


def csv_stock_h5(request, symbol):
    """
    Import csv files stock data only
    /stock/gld
    :param request: request
    :param symbol: str
    :return: render
    """
    symbol = symbol.lower()

    # remove all
    db = pd.HDFStore(QUOTE)
    try:
        db.remove('stock/thinkback/%s' % symbol.lower())
    except KeyError:
        pass
    db.close()

    # get underlying
    underlying = Underlying.objects.get(symbol=symbol.upper())
    start = underlying.start
    end = underlying.stop

    # move files into year folder
    path = os.path.join(BASE_DIR, 'files', 'thinkback', symbol)
    no_year_files = glob(os.path.join(path, '*.csv'))
    years = sorted(list(set([os.path.basename(f)[:4] for f in no_year_files])))

    for year in years:
        year_dir = os.path.join(path, year)

        # make dir if not exists
        if not os.path.isdir(year_dir):
            os.mkdir(year_dir)

        # move all year files into dir
        for no_year_file in no_year_files:
            filename = os.path.basename(no_year_file)
            if filename[:4] == year:
                try:
                    os.rename(no_year_file, os.path.join(year_dir, filename))
                except WindowsError:
                    # remove old file, use new file
                    os.remove(os.path.join(year_dir, filename))
                    os.rename(no_year_file, os.path.join(year_dir, filename))
                    pass

    # only get valid date
    trading_dates = pd.Series([d.date() for d in pd.bdate_range(start, end)])
    trading_dates = np.array(
        trading_dates[
            trading_dates.apply(lambda x: not offday(x) and not holiday(x))
        ].apply(lambda x: x.strftime('%Y-%m-%d'))
    )

    files = []
    for year in glob(os.path.join(path, '*')):
        for csv in glob(os.path.join(year, '*.csv')):
            # skip date if not within underlying dates
            if os.path.basename(csv)[:10] in trading_dates:
                files.append(csv)

    # start save csv
    error_dates = list()
    stocks = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}
    for i, f in enumerate(sorted(files)):
        # get date and symbol
        fdate, _ = os.path.basename(f)[:-4].split('-StockAndOptionQuoteFor')

        bday = pd.datetime.strptime(fdate, '%Y-%m-%d').date()
        trading_day = not (holiday(bday) or offday(bday))

        if trading_day:
            # output to console
            stock_data, option_data = ThinkBack(f).read()

            try:
                if int(stock_data['volume']) == 0:
                    error_dates.append(fdate)
                    continue  # skip this part
            except ValueError:
                continue

            # save stock
            stocks['date'].append(pd.to_datetime(stock_data['date']))
            stocks['open'].append(float(stock_data['open']))
            stocks['high'].append(float(stock_data['high']))
            stocks['low'].append(float(stock_data['low']))
            stocks['close'].append(float(stock_data['last']))
            stocks['volume'].append(int(stock_data['volume']))
    else:
        df_stock = pd.DataFrame(stocks)
        df_stock['open'] = np.round(df_stock['open'], 2)
        df_stock['high'] = np.round(df_stock['high'], 2)
        df_stock['low'] = np.round(df_stock['low'], 2)
        df_stock['close'] = np.round(df_stock['close'], 2)

        if len(df_stock):
            df_stock = df_stock.set_index('date')

            quote = pd.HDFStore(QUOTE)
            quote.append('stock/thinkback/%s' % symbol, df_stock,
                         format='table', data_columns=True)
            quote.close()

    # check missing dates
    df_exist = get_exist_stocks(symbol)

    missing = list()
    bdays = pd.bdate_range(start=start, end=end, freq='B')
    for bday in bdays:
        if holiday(bday.date()) or offday(bday.date()):
            continue

        if bday not in df_exist.index:
            missing.append(bday.strftime('%m/%d/%Y'))

    # update underlying
    underlying.thinkback = len(df_exist)
    underlying.missing = '\n'.join(missing)
    underlying.save()

    # stats
    stats = {'count': len(df_stock), 'start': start, 'stop': end}

    completes = [{'date': i.strftime('%Y-%m-%d'), 'volume': v['volume'], 'close': round(v['close'], 2)}
                 for i, v in df_stock.iterrows()]

    # view
    template = 'data/csv_stock_h5.html'

    parameters = dict(
        site_title='Csv Stock import',
        title='Thinkback csv stock import: {symbol}'.format(symbol=symbol.upper()),
        symbol=symbol,
        stats=stats,
        completes=completes,
        missing=missing
    )

    return render(request, template, parameters)


# noinspection PyUnresolvedReferences
def csv_option_h5(request, symbol):
    """
    Import thinkback csv options into db,
    every time this run, it will start from first date

    /option/gld/date -> keep all inserted date
    /option/gld/contract -> GLD150117C114 data
    /option/gld/code/GLD7150102C110 -> values

    how do you get daily all delta > 0.5 option?
    if timeout when running script, remember change browser timeout value
    :param request: request
    :param symbol: str
    :return: render
    """
    symbol = symbol.lower()
    path = os.path.join(BASE_DIR, 'files', 'thinkback', symbol)
    df_stock = get_exist_stocks(symbol)

    # open db
    db = pd.HDFStore(QUOTE)

    # remove all existing data
    for key in ('date', 'index', 'contract', 'raw', 'clean', 'data'):
        try:
            db.remove('option/%s/%s' % (symbol, key))
        except KeyError:
            pass

    # all new
    df_contract = pd.DataFrame(columns=[
        'option_code',
        'ex_date', 'ex_month', 'ex_year', 'expire',
        'name', 'others', 'right', 'special', 'strike'
    ])
    dc_index = {}
    options = {}

    # start loop every date
    inserted = 0
    for index, values in df_stock.iterrows():
        # open path get option data
        year = index.date().strftime('%Y')
        fpath = os.path.join(
            path, year, '%s-StockAndOptionQuoteFor%s.csv' % (
                index.date().strftime('%Y-%m-%d'), symbol.upper()
            )
        )
        _, option_data = ThinkBack(fpath).read()

        # get all contract
        contracts = [c for c, _ in option_data]

        # date code index
        if len(contracts):
            for c in contracts:
                if c['option_code'] in dc_index.keys():
                    dc_index[c['option_code']].append(index)
                else:
                    dc_index[c['option_code']] = [index]

        print 'D | %-12s | ' % index.strftime('%Y-%m-%d'), 'CONTRACT: %-7s | ' % len(contracts),
        print 'INDEX LENGTH: %-10s | ' % len(dc_index.keys()),

        # get new contract and a list of no list code
        option_code = np.array(df_contract[df_contract['expire'] == False]['option_code'])
        df_remain = df_contract[df_contract['expire'] == False]  # get no expire contract

        # speed up matching using string matching
        contract_keys = ['option_code', 'name', 'ex_month', 'ex_year',
                         'special', 'strike', 'right', 'others']
        option_set = []
        for _, data in df_remain.iterrows():
            option_set.append(','.join([str(data[key]) for key in contract_keys]))

        new_contract = []
        for c in contracts:
            # matching whole
            spec0 = ','.join([str(c[key]) for key in contract_keys])
            if spec0 in option_set:
                # full set match
                df_remain = df_remain[df_remain['option_code'] != c['option_code']]
                continue
            elif c['option_code'] in option_code:
                # update if exists but full spec not same
                q = df_contract['option_code'] == c['option_code']
                t = df_contract[q].iloc[0]
                # only code is match
                found = False
                for key in contract_keys:
                    if c[key] != t[key]:
                        print 'C | %-12s | %-27s | %-14s => %-14s' % (
                            'CONTRACT',
                            'DETAIL CHANGE %s' % c['option_code'],
                            c[key],
                            t[key]
                        )
                        df_contract.loc[q, key] = c[key]

                        found = True

                if found:
                    df_remain = df_remain[df_remain['option_code'] != c['option_code']]
            else:
                # no match at all
                c['ex_date'] = pd.Timestamp(get_dte_date(c['ex_month'], int(c['ex_year'])))
                c['expire'] = 0

                new_contract.append(c)

        p = True
        if len(df_remain):
            for n in [n for n in new_contract]:
                # new is not in option code, so we need to check spec is same
                update = 0
                code0 = ''
                code1 = n['option_code']
                query = [
                    'name == %r' % n['name'],
                    'ex_month == %r' % n['ex_month'],
                    'ex_year == %r' % n['ex_year'],
                    'strike == %r' % n['strike'],
                    'special == %r' % n['special'],
                    'right == %r' % n['right'],
                    'others == %r' % n['others']
                ]

                # full found on everything is same
                found0 = df_remain.query(' & '.join(query))
                if len(found0) == 1:
                    update = 1
                    code0 = found0['option_code'][found0.index.values[0]]
                elif len(found0) > 1:
                    print found0.to_string(line_width=1000)
                    raise LookupError('%s found %d similar full specs' % (n['option_code'], len(found0)))

                # got others, special div, announcement
                found1 = df_remain.query(' & '.join(query[:-1]))  # without others
                if not update and len(found1) == 1:
                    update = 2
                    code0 = found1['option_code'][found1.index.values[0]]
                elif len(found1) > 1:
                    print found1.to_string(line_width=1000)
                    raise LookupError('%s found %d others specs' % (n['option_code'], len(found1)))

                # got split or bonus issue or etc...
                found2 = df_remain.query(' & '.join(query[:-2]))  # without others and right
                if not update and len(found2) == 1:
                    update = 3
                    code0 = found2['option_code'][found2.index.values[0]]
                elif len(found2) > 2:
                    print found2.to_string(line_width=1000)
                    raise LookupError('%s found %d others right specs' % (n['option_code'], len(found2)))

                if update:
                    if p:
                        print ''
                        p = False

                    print 'C | %-12s | %-27s | %-14s => %-14s' % (
                        'CODE CHANGE',
                        [
                            '',
                            'NORMAL (Old to new format)',
                            'OTHERS (Special dividend or etc)',
                            'RIGHT (Split, bonus issue or etc)',
                        ][update],
                        code0,
                        code1
                    )

                    # remove code from df_remain
                    df_remain = df_remain[df_remain['option_code'] != code0]

                    # remove contract code from df_contract
                    df_contract.loc[df_contract['option_code'] == code0, 'option_code'] = code1
                    # update all
                    df_contract.loc[df_contract['option_code'] == code1, 'others'] = n['others']
                    df_contract.loc[df_contract['option_code'] == code1, 'right'] = n['right']

                    # update option data from old key name into new key name
                    options[code1] = []
                    if code0 in options.keys():
                        options[code1] += options[code0]
                        del options[code0]  # remove option data in new data

                        for i, o in enumerate(options[code1]):
                            options[code1][i]['option_code'] = code1

                    # update date code index
                    dc_index[code1] = []
                    if code0 in options.keys():
                        dc_index[code1] += dc_index[code0]
                        del dc_index[code0]  # remove option data in new data

                        for i, o in enumerate(dc_index[code1]):
                            dc_index[code1][i]['option_code'] = code1

                    # remove from new contract list
                    del new_contract[new_contract.index(n)]

        # set missing
        if len(df_remain):
            print 'ACTIVE: %-6d | ' % len(df_contract[df_contract['expire'] == False]),
            print 'MISSING: %-6d' % len(df_remain)

            for _, c in df_remain.iterrows():
                # if expire skip it
                q = df_contract['option_code'] == c['option_code']
                q &= df_contract['ex_date'] >= index

                df_contract.loc[q, 'missing'] += 1
        else:
            print 'ACTIVE:  %-6d | ' % len(df_contract[df_contract['expire'] == False]),
            print 'NO MISSING'

        # insert new contract into df_contract
        if len(new_contract):
            # add new contract into df_contract
            df = pd.DataFrame(new_contract)
            df['expire'] = df['expire'].astype('bool')
            df['missing'] = 0
            if len(df_contract):
                df_contract = pd.concat([df_contract, df])
            else:
                df_contract = df

        # insert option into big option data list
        for c, o in option_data:
            o['date'] = index
            o['option_code'] = c['option_code']

            if c['option_code'] in options.keys():
                if float(o['bid']) >= float(o['ask']):
                    continue  # bid must less than ask price

                if float(o['bid']) > 0 or float(o['ask']) > 0:  # only bid or ask > 0
                    options[c['option_code']].append(o)
            else:
                options[c['option_code']] = [o]

        # expire, save into db and delete from new and old
        q0 = df_contract['ex_date'] <= index
        q1 = df_contract['expire'] == False
        if np.any(q0 & q1):
            # change old format into new format, if not yet change
            for _, c in df_contract[q0 & q1].iterrows():
                old_code, new_code = new_code_format(symbol, c, df_contract)

                if len(new_code):
                    options[new_code] = options[old_code]
                    del options[old_code]

                    for i, o in enumerate(options[new_code]):
                        options[new_code][i]['option_code'] = new_code

            ex_data = []
            for _, c in df_contract[q0 & q1].iterrows():
                inserted += 1
                try:
                    ex_data += options[c['option_code']]
                except KeyError:
                    print df_contract[df_contract['option_code'] == c['option_code']]
                    raise KeyError('No option code found %s' % c['option_code'])

                print 'E | OPTION %-5d | %-30s | %-20s | %-6d' % (
                    inserted,
                    'EXPIRE & INSERT OPTION CODE',
                    c['option_code'],
                    len(options[c['option_code']])
                )
                del options[c['option_code']]

            df_expire = pd.DataFrame(ex_data, index=range(len(ex_data))).set_index('date')
            db.append(
                'option/%s/raw' % symbol, df_expire,
                format='table', data_columns=True, min_itemsize=100
            )

            # set all expire
            df_contract.loc[q0 & q1, 'expire'] = True

    df_index = pd.DataFrame()
    if len(dc_index.keys()):
        dc_data = []
        for code, dates in dc_index.items():
            for d in dates:
                dc_data.append({
                    'date': d,
                    'option_code': code
                })

        df_index = pd.DataFrame(dc_data, index=range(len(dc_data))).set_index('date')
        db.append(
            'option/%s/index' % symbol, df_index,
            format='table', data_columns=True, min_itemsize=100
        )

    if len(df_contract):
        # old code to new code
        for _, c in df_contract.iterrows():
            old_code, new_code = new_code_format(symbol, c, df_contract)

            if len(new_code):
                options[new_code] = options[old_code]
                del options[old_code]

                for i, o in enumerate(options[new_code]):
                    options[new_code][i]['option_code'] = new_code

        # save into db
        db.append(
            'option/%s/contract' % symbol, df_contract,
            format='table', data_columns=True, min_itemsize=100
        )

    if len(options):
        # finish, insert all new_data
        data = []
        for k, l in options.items():
            inserted += 1
            for v in l:
                data.append(v)
            del options[k]  # remove in options

            print 'I | OPTION %-5d | INSERT OPTION CODE: %-20s | LENGTH: %-5s' % (inserted, k, len(l))

        df_data = pd.DataFrame(data, index=range(len(data))).set_index('date')
        db.append(
            'option/%s/raw' % symbol, df_data,
            format='table', data_columns=True, min_itemsize=100
        )

    missing = []
    df_missing = db.select('option/%s/contract' % symbol, 'missing > 0')
    if len(df_missing):
        for _, m in df_missing.sort_values(by='missing', ascending=False).iterrows():
            missing.append({
                'option_code': m['option_code'],
                'count': m['missing']
            })

    completed = []
    if len(df_index):
        for i in df_index.index.unique():
            completed.append({
                'date': i.date(),
                'count': len(df_index.ix[i]),
            })

    df_data = db.select('option/%s/raw' % symbol)
    df_contract = db.select('option/%s/contract' % symbol)
    stats = {
        'data': len(df_data),
        'index': len(df_index),
        'contract': len(df_contract),
        'expire': len(df_contract[df_contract['expire']]),
        'active': len(df_contract[df_contract['expire'] == False]),
        'right': ', '.join(df_contract['right'].unique()),
        'others': ', '.join(df_contract[df_contract['others'] != '']['others'].unique()),
        'special': ', '.join(df_contract['special'].unique())
    }

    # close db
    db.close()

    # update underlying
    underlying = Underlying.objects.get(symbol=symbol.upper())
    underlying.contract = len(df_contract)
    underlying.option = len(df_data)
    underlying.save()

    template = 'data/csv_option_h5.html'
    parameters = dict(
        site_title='Csv option import',
        title='Thinkback csv option import: {symbol}'.format(symbol=symbol.upper()),
        symbol=symbol.upper(),
        stats=stats,
        missing=missing,
        completed=completed
    )

    return render(request, template, parameters)