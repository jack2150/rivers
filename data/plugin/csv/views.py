import calendar
from fractions import Fraction
from glob import glob
import os
import re
import time
from django.shortcuts import render
from numba import jit
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
    # noinspection PyUnresolvedReferences
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
            print '%-05d | %-20s' % (i, os.path.basename(f))
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


@jit
def valid_option(bid, ask, volume, open_int, dte):
    valid = np.ones(len(bid), dtype='int')

    for i in range(len(valid)):
        if ask[i] < 0:
            valid[i] = 0

        if bid[i] < 0:
            valid[i] = 0

        if bid[i] >= ask[i]:
            valid[i] = 0

        if volume[i] < 0:
            valid[i] = 0

        if open_int[i] < 0:
            valid[i] = 0

        if dte[i] < 0:
            valid[i] = 0

    return valid


def valid_code(option_code0, option_code1):
    """
    Check every option_code is exists in df_option
    :param option_code0: list
    :param option_code1: list
    :return: list
    """
    valid = np.ones(len(option_code0), dtype='int')
    codes = list(option_code1)
    for i in range(len(option_code0)):
        if option_code0[i] not in codes:
            valid[i] = 0

    return valid


def valid_contract(symbol, df_contract):
    """
    Valid df_contract every column
    :param symbol: str
    :param df_contract: DataFrame
    :return: list
    """
    valid = np.ones(len(df_contract), dtype='int')
    specials = ['Standard', 'Weeklys', 'Quarterlys', 'Mini']
    months = [calendar.month_name[i + 1][:3].upper() for i in range(12)]
    years = range(8, 20)
    weeks = range(1, 7)
    for i, (_, contract) in enumerate(df_contract.iterrows()):
        if symbol not in contract['option_code']:
            valid[i] = 0

        if contract['ex_month'][:3] not in months:
            valid[i] = 0

        if len(contract['ex_month']) == 4:
            if int(contract['ex_month'][3:]) not in weeks:
                valid[i] = 0

        if contract['ex_year'] not in years:
            valid[i] = 0

        if type(contract['expire']) is not bool:
            valid[i] = 0

        if type(contract['ex_date']) is not pd.Timestamp:
            valid[i] = 0

        if contract['missing'] < 0:
            valid[i] = 0

        # right
        if '/' in contract['right']:
            try:
                Fraction(contract['right'])
            except ValueError:
                valid[i] = 0
        else:
            try:
                int(contract['right'])
            except ValueError:
                valid[i] = 0

        if contract['special'] not in specials:
            valid[i] = 0

        if type(contract['strike']) is not float:
            valid[i] = 0

    return valid


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
    # noinspection PyUnresolvedReferences
    path = os.path.join(BASE_DIR, 'files', 'thinkback', symbol)
    df_stock = get_exist_stocks(symbol)

    # open db
    db = pd.HDFStore(QUOTE)

    # remove all existing data
    try:
        db.remove('option/%s' % symbol)
    except KeyError:
        pass

    # all new
    df_contract = pd.DataFrame(columns=[
        'option_code',
        'ex_date', 'ex_month', 'ex_year', 'expire',
        'name', 'others', 'right', 'special', 'strike',
        'missing'
    ])
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

        # output
        print 'D | %-12s | CONTRACT: %-7s | ' % (index.strftime('%Y-%m-%d'), len(contracts)),

        # df_remain: all previous option_code that not expire
        # df_new: all current file option_code
        # df_continue: all option_code in new and remain
        # make a list of remain option_code
        df_remain = df_contract[df_contract['expire'] == False].copy(deep=True)  # get no expire contract
        df_all = pd.DataFrame(contracts)
        df_continue = pd.merge(
            df_all, df_remain, how='inner', on=[
                'option_code', 'name', 'ex_month', 'ex_year',
                'special', 'strike', 'right', 'others'
            ]
        )
        df_new = df_all[~df_all['option_code'].isin(df_continue['option_code'])]
        df_remain = df_remain[~df_remain['option_code'].isin(df_continue['option_code'])]

        # check remain option_code is still exists, then change detail
        if len(df_contract) and len(df_remain) and len(df_new):
            df_change = pd.merge(
                df_contract[
                    ['option_code', 'strike', 'name', 'ex_date',
                     'ex_month', 'ex_year', 'expire', 'missing']
                ],
                df_new[df_new['option_code'].isin(df_remain['option_code'])][
                    ['option_code', 'strike', 'special', 'right', 'others']
                ],
                how='inner', on=['option_code', 'strike']
            )

            # merge back
            df_contract = pd.concat([
                df_contract[~df_contract['option_code'].isin(df_change['option_code'])],
                df_change
            ])
            """:type: pd.DataFrame"""

            # reduce df_new and df_remain
            df_new = df_new[~df_new['option_code'].isin(df_change['option_code'])]
            df_remain = df_remain[~df_remain['option_code'].isin(df_change['option_code'])]

            for _, c in df_change.iterrows():
                print 'C | %-12s | %-27s' % (
                    'CONTRACT',
                    'DETAIL CHANGE %s' % c['option_code']
                )

        # all remaining new option_code that not full match or detail change
        if len(df_new):
            df_new.loc[:, 'expire'] = False
            df_new.loc[:, 'ex_date'] = df_new.apply(
                lambda x: pd.Timestamp(get_dte_date(x['ex_month'], int(x['ex_year']))), axis=1
            )

        # df_new that same spec in df_remain
        if len(df_remain) and len(df_new):
            keys = ['option_code', 'name', 'ex_month', 'ex_year', 'strike', 'special', 'right', 'others']
            count = {
                'df_remain': len(df_remain),
                'df_new': len(df_new),
                'df_contract': len(df_contract),
            }
            for i in range(len(keys), len(keys) - 3, -1):

                df_spec = pd.merge(
                    df_remain.rename(columns={'option_code': 'old_code'}),
                    df_new[keys[:i]],
                    how='inner', on=keys[1:i]
                )

                for _, c in df_spec.iterrows():
                    print 'C | %-12s | %-27s | %-14s => %-14s' % (
                        'CODE CHANGE',
                        [
                            'RIGHT (SPLIT, BONUS ISSUE OR ETC)',
                            'OTHERS (SPECIAL DIVIDEND OR ETC)',
                            'NORMAL (OLD CODE TO NEW CODE)',
                        ][i - 6],
                        c['old_code'],
                        c['option_code']
                    )

                    # update option_code in options data
                    options[c['option_code']] = options[c['old_code']]
                    del options[c['old_code']]  # remove option data in new data

                    for j, __ in enumerate(options[c['option_code']]):
                        options[c['option_code']][j]['option_code'] = c['option_code']

                if len(df_contract) and len(df_spec):
                    # update current contract that change code, others, right
                    df_update = pd.merge(
                        df_contract[[
                            'ex_date', 'ex_month', 'ex_year', 'expire', 'missing', 'name',
                            'option_code', 'special', 'strike'
                        ]].rename(columns={'option_code': 'old_code'}),
                        df_spec[['old_code', 'option_code', 'others', 'right']].rename(
                            columns={'option_code': 'new_code'}
                        ),
                        how='inner', on='old_code'
                    ).rename(columns={'new_code': 'option_code'})
                    df_contract = df_contract[~df_contract['option_code'].isin(df_spec['old_code'])]
                    df_contract = pd.concat([df_contract, df_update])
                    """:type: pd.DataFrame"""
                    del df_contract['old_code']

                    assert len(df_contract) == count['df_contract']

                    # remove found spec old code in df_remain then merge df_spec back into it
                    df_remain = df_remain[~df_remain['option_code'].isin(df_spec['old_code'])]
                    del df_spec['old_code']

                    # remove found new option_code in df_new
                    df_new = df_new[~df_new['option_code'].isin(df_spec['option_code'])]

                    assert len(df_remain) <= count['df_remain']
                    assert len(df_new) <= count['df_new']

        # set missing
        if len(df_remain):
            print 'ACTIVE: %-6d | ' % len(df_contract[df_contract['expire'] == False]),
            print 'MISSING: %-6d' % len(df_remain)

            df_contract.loc[
                (df_contract['option_code'].isin(df_remain['option_code']) &
                 df_contract['ex_date'].apply(lambda x: x >= index)),
                'missing'
            ] += 1
        else:
            print 'ACTIVE:  %-6d | ' % len(df_contract[df_contract['expire'] == False]),
            print 'NO MISSING'

        # insert new contract into df_contract
        if len(df_new):
            # add new contract into df_contract
            df_new.loc[:, 'expire'] = df_new['expire'].astype('bool')
            df_new.loc[:, 'missing'] = 0
            if len(df_contract):
                df_contract = pd.concat([df_contract, df_new])
            else:
                df_contract = df_new

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
        q0 = df_contract['ex_date'].apply(lambda x: x <= index)
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
                'option/%s/raw/data' % symbol, df_expire,
                format='table', data_columns=True, min_itemsize=100
            )

            # set all expire
            # noinspection PyUnresolvedReferences
            df_contract.loc[q0 & q1, 'expire'] = True

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
            'option/%s/raw/contract' % symbol, df_contract,
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
            'option/%s/raw/data' % symbol, df_data,
            format='table', data_columns=True, min_itemsize=100
        )

    missing = []
    try:
        df_missing = db.select('option/%s/raw/contract' % symbol, 'missing > 0')
        if len(df_missing):
            for _, m in df_missing.sort_values(by='missing', ascending=False).iterrows():
                missing.append({
                    'option_code': m['option_code'],
                    'count': m['missing']
                })
    except KeyError:
        pass

    # validating
    df_contract = db.select('option/%s/raw/contract' % symbol)
    df_contract = df_contract.copy().reset_index()
    df_data = db.select('option/%s/raw/data' % symbol)
    df_data = df_data.copy().reset_index()

    df_data['valid'] = valid_option(
        df_data['bid'], df_data['ask'], df_data['volume'], df_data['open_int'], df_data['dte']
    )
    df_data = df_data.query('valid == 1')
    df_data = df_data.set_index('date')
    del df_data['valid']

    df_contract['valid'] = valid_code(
        list(df_contract['option_code']), df_data['option_code'].unique()
    )
    df_contract = df_contract.query('valid == 1')
    del df_contract['valid']
    df_contract = df_contract.copy()

    df_contract['valid'] = valid_contract(symbol.upper(), df_contract)
    df_contract = df_contract.query('valid == 1')
    del df_contract['valid']

    # save back into db
    db.remove('option/%s/raw/contract' % symbol)
    db.remove('option/%s/raw/data' % symbol)

    db.append('option/%s/raw/contract' % symbol, df_contract)
    db.append('option/%s/raw/data' % symbol, df_data)

    # output html
    stats = {
        'data': len(df_data),
        'index': len(df_data.index.unique()),
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
        missing=missing
    )

    return render(request, template, parameters)