import calendar
import os
import re
import time
from fractions import Fraction
from django.shortcuts import render
from numba import jit
from data.plugin.csv.views import get_exist_stocks, get_dte_date
from data.plugin.thinkback import ThinkBack
from rivers.settings import BASE_DIR
import numpy as np
import pandas as pd


specials = ['Standard', 'Weeklys', 'Quarterlys', 'Mini']
months = [calendar.month_name[m + 1][:3].upper() for m in range(12)]
years = range(8, 20)
weeks = range(1, 7)
output = '%-6s | %-30s %s'


def make_code2(symbol, others, right, special, ex_date, name, strike, extra=''):
    """
    Make new option code using contract data
    :param symbol:
    :param others:
    :param right:
    :param special:
    :param ex_date:
    :param name:
    :param strike:
    :return:
    :return: str
    """
    if extra == '':
        if special == 'Mini':
            extra = 7
        elif '; US$' in others:
            extra = 2
        elif 'US$' in others:
            extra = 1
        elif '/' in right:
            extra = 1

    strike = str(strike)
    if strike[-2:] == '.0':
        strike = strike.replace('.0', '')

    new_code = '{symbol}{extra}{year}{month}{day}{name}{strike}'.format(
        symbol=symbol.upper(),
        extra=extra,
        year=ex_date.date().strftime('%y'),
        month=ex_date.date().strftime('%m'),
        day=ex_date.date().strftime('%d'),
        name=name[0].upper(),
        strike=strike
    )

    return new_code


def change_code(symbol, code, others, right, special):
    """
    Make new option code using contract data
    :param symbol:
    :param code:
    :param others:
    :param right:
    :param special:
    :return:
    :return: str
    """
    extra = ''
    if special == 'Mini':
        extra = 7
    elif '; US$' in others:
        extra = 2
    elif 'US$' in others:
        extra = 1
    elif '/' in right:
        extra = 1

    wrong = re.search('^([A-Z]+)\d+[CP]+\d+', code).group(1)

    new_code = '{symbol}{extra}{right}'.format(
        symbol=symbol.upper(), extra=extra, right=code[len(wrong):]
    )

    return new_code


@jit
def valid_option2(index, bid, ask, volume, open_int, dte):
    valid = np.ones(len(index), dtype='int')

    for i, j in enumerate(index):
        if ask[j] < 0:
            valid[i] = 0

        if bid[j] < 0:
            valid[i] = 0

        if bid[j] >= ask[j]:
            valid[i] = 0

        if volume[j] < 0:
            valid[i] = 0

        if open_int[j] < 0:
            valid[i] = 0

        if dte[j] < 0:
            valid[i] = 0

    return valid


def valid_contract2(ex_month, ex_year, right, special):
    """
    Valid df_contract every column
    :param ex_month:
    :param ex_year:
    :param right:
    :param special:
    :return: list
    """
    valid = np.ones(len(ex_month), dtype='int')

    for i in range(len(ex_month)):
        if ex_month[i][:3] not in months:
            valid[i] = 0

        if len(ex_month[i]) == 4:
            if int(ex_month[i][3:]) not in weeks:
                valid[i] = 0

        if ex_year[i] not in years:
            valid[i] = 0

        if '/' in right[i]:
            try:
                Fraction(right[i])
            except ValueError:
                valid[i] = 0
        else:
            try:
                int(right[i])
            except ValueError:
                valid[i] = 0

        if special[i] not in specials:
            valid[i] = 0

    return valid


def add_remain(contracts, options, df_save, df_stock, symbol):
    contract = get_contract(df_save)
    contract['option_code'] = check_code(symbol, contract)
    df_save['option_code'] = contract['option_code']
    print output % (len(contracts), 'Append contract and option:', '%-16s %d' % (
        contract['option_code'], len(df_save)
    ))
    check_date(df_save)

    # basic valid option here
    df_save['valid'] = valid_option2(
        df_save.index, df_save['bid'], df_save['ask'],
        df_save['volume'], df_save['open_int'], df_save['dte']
    )
    df_save = df_save[df_save['valid'] == 1]
    del df_save['valid']

    # set missing
    if len(df_save) > 1:
        latest = df_save['date'].iloc[0]
        oldest = df_save['date'].iloc[-1]
        length = np.sum((oldest <= df_stock.index) & (df_stock.index <= latest))
    else:
        length = 1

    contract['missing'] = length - len(df_save)

    # print df_save.to_string(line_width=1000)

    contracts.append(contract)
    options.append(df_save)


def add_contract(symbol, df_current, df_save, df_stock, contracts, options):
    df_current, df_save = join_remain(df_current, df_save)
    add_remain(contracts, options, df_save, df_stock, symbol)

    return df_current


def get_contract(df_current):
    return df_current.iloc[0][[
        'ex_month', 'ex_year', 'name', 'option_code',
        'others', 'right', 'special', 'strike'
    ]]


def join_remain(df_current, df_start):
    df_start = pd.concat([
        df_start, df_current.query('date < %r' % df_start['date'].iloc[-1])
    ])
    """:type: pd.DataFrame"""
    df_current = df_current[~df_current.index.isin(df_start.index)]

    return df_current, df_start


def check_date(df):
    """

    :param df: pd.DataFrame
    :return:
    """
    if len(df) != len(df['date'].unique()):
        print df.to_string(line_width=1000)
        d = df['date'].value_counts()
        print d[d >= 2]

        raise IndexError('Duplicate date in dataframe')


def check_code(symbol, contract):
    if len(contract['option_code']) < 9:  # old format or no symbol
        ex_date = pd.Timestamp(get_dte_date(contract['ex_month'], int(contract['ex_year'])))

        new_code = make_code2(
            symbol, contract['others'], contract['right'], contract['special'],
            ex_date, contract['name'], contract['strike']
        )
        print output % ('CODE', 'Update (old format):', '%-16s -> %-16s' % (
            contract['option_code'], new_code
        ))
    elif contract['option_code'][:len(symbol)] != symbol.upper():
        # some ex_date is on thursday because holiday or special date
        new_code = change_code(
            symbol, contract['option_code'], contract['others'], contract['right'], contract['special']
        )
        print output % ('CODE', 'Update (no symbol):', '%-16s -> %-16s' % (
            contract['option_code'], new_code
        ))
    else:
        new_code = contract['option_code']

    return new_code


def multi_others(symbol, contracts, options, df_current, df_stock):
    """

    :param symbol: str
    :param contracts: list
    :param options: list
    :param df_stock: pd.DataFrame
    :param df_current: pd.DataFrame
    :return: pd.DataFrame
    """
    print output % ('OTHERS', 'MULTI OTHERS FOUND', 'PROCESSING')

    rights = {}
    for i, code in enumerate(df_current['option_code'].unique(), start=1):
        if len(df_current) == 0:
            continue

        data = []
        df_temp = df_current[df_current['option_code'] == code].copy()
        rights[code] = df_temp['right'].iloc[0]
        for date in df_current['date'].unique():
            df_date = df_current[
                (df_current['option_code'] == code) &
                (df_current['date'] == date)
                ]

            if len(df_date):
                # option_code match
                data.append(df_date)

                continue
            else:
                df_similar = df_current[
                    (df_current['date'] == date) &
                    (df_current['right'] == rights[code])
                    ]

                if len(df_similar):
                    # save, then update code
                    new_code = df_similar['option_code'].iloc[0]
                    data.append(df_date)

                    rights[new_code] = rights[code]
                    del rights[code]
                    code = new_code

        df_temp = pd.concat(data)
        """:type: pd.DataFrame"""
        contract = get_contract(df_temp)
        ex_date = pd.Timestamp(get_dte_date(contract['ex_month'], int(contract['ex_year'])))
        new_code = make_code2(
            symbol, contract['others'], contract['right'], contract['special'],
            ex_date, contract['name'], contract['strike'], '%d' % i
        )

        df_temp['option_code'] = new_code

        d = df_temp['date'].value_counts()

        """:type: pd.DataFrame"""
        df_current = add_contract(symbol, df_current, df_temp, df_stock, contracts, options)


def csv_option_h5x(request, symbol):
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
    df_stock = get_exist_stocks(symbol).sort_index(ascending=False)
    last_date = df_stock.index[0]

    """
    keys = []
    options = []
    for i, (index, values) in enumerate(df_stock.iterrows()):
        # open path get option data
        year = index.date().strftime('%Y')
        fpath = os.path.join(
            path, year, '%s-StockAndOptionQuoteFor%s.csv' % (
                index.date().strftime('%Y-%m-%d'), symbol.upper()
            )
        )
        print output % (i, 'read thinkback file:', fpath)
        _, data = ThinkBack(fpath).read()

        for contract, option in data:
            index = '%s%s%s%s' % (
                contract['ex_month'], contract['ex_year'], contract['name'], contract['strike']
            )

            try:
                key = keys.index(index)
            except ValueError:
                keys.append(index)
                key = keys.index(index)

            contract['index'] = index
            contract['key'] = key

            option.update(contract)

            options.append(option)

    # make all options df
    df_all = pd.DataFrame(options)
    df_all['date'] = pd.to_datetime(df_all['date'])
    # print df_all.head().to_string(line_width=1000)


    # testing

    db = pd.HDFStore('test.h5')
    for key in ('option', 'tkeys'):
        try:
            db.remove(key)
        except KeyError:
            pass
    db.append('option', df_all)
    db.append('tkeys', pd.Series(keys))
    db.close()
    exit()
    """

    db = pd.HDFStore('test.h5')
    df_all = db.select('option')
    df_all = df_all.sort_values('date', ascending=False)
    keys = db.select('tkeys')
    db.close()

    panel = []
    size = 100
    for i in range(0, len(keys), size):
        df_size = df_all.query('%r <= key < %r' % (i, i + size))
        for j, k in enumerate(keys[i:i + size], start=i):
            df_current = df_size.query('key == %r' % j)
            print output % (j, 'Get df_current from df_all:', '%-16s %d' % (k, len(df_current)))
            if len(df_current):
                panel.append(df_current)

    # df_test = df_all.query('option_code == "AIG140517C49"') # normal
    # df_test = df_all.query('option_code == "UZLAT" | option_code == "AILAT"')  # split
    # df_test = df_all.query('option_code == "AIG2110219C52.5" | option_code == "AIG110219C52.5"')  # add others
    # df_test = df_all.query('index == "MAR10CALL33.0"')  # wrong symbol
    # df_test = df_all[df_all['index'].isin(["AUG10CALL25.0"])]  # code change normal
    # df_test = df_all[df_all['index'] == 'JAN11CALL5.0']  # code change, split, special dividend,
    # df_test = df_all[df_all['option_code'] == 'AIG110701P23']  # code change, split, special dividend,
    # df_test = df_all[df_all['index'] == 'JAN10CALL70.0']  # code change, split, special dividend,
    # df_test = df_all[df_all['index'] == 'APR9CALL10.0']  # double others
    # df_test = df_all[df_all['index'] == 'APR9CALL25.0']  # double others
    # df_test = df_all[df_all['option_code'].isin(['DDD140118C30', 'DDD1140118C30'])]  # double others
    # df_test = df_all[df_all['index'].isin(['JAN15CALL30.0'])]  # double others
    # panel = [df_test]
    # print df_test.to_string(line_width=1000)
    # print df_all.to_string(line_width=1000)
    # print df_all.head().to_string(line_width=1000)
    # print keys

    contracts = []
    options = []
    # start matching
    for key, df_current in enumerate(panel):
        df_current = df_current.copy()
        # print df_current.to_string(line_width=1000)
        # print len(df_current)
        if len(df_current) != len(df_current['date'].unique()):
            df_current.loc[df_current['others'] == 'Non Standard', 'others'] = ""
            others = df_current.loc[df_current['others'] != '', 'others'].unique()
            right = df_current.loc[df_current['right'] != '100', 'right'].unique()

            df_others = pd.DataFrame()
            if len(others):
                df_others = df_current.query('others != ""')


                if len(df_others) != len(df_others['date'].unique()):
                    multi_others(symbol, contracts, options, df_current, df_stock)
                    continue

                if len(df_others) == 1:  # DDD 150 for split
                    df_others = pd.DataFrame()

            df_right = pd.DataFrame()
            if len(right):
                df_right = df_current.query('right != "100"')

            if len(df_others) and len(df_right):
                if len(df_others) > len(df_right):
                    # all others data + normal before
                    df_current = add_contract(symbol, df_current, df_others, df_stock, contracts, options)

                    # all right data + normal before
                    df_current = add_contract(symbol, df_current, df_right, df_stock, contracts, options)

                    # if still have left, then is all normal
                    if len(df_current):
                        df_remain = df_current.copy()
                        add_remain(contracts, options, df_remain, df_stock, symbol)

                elif len(df_others) < len(df_right):
                    # all right data + normal before
                    df_current = add_contract(symbol, df_current, df_right, df_stock, contracts, options)

                    # all others data + normal before
                    df_current = add_contract(symbol, df_current, df_others, df_stock, contracts, options)

                    # if still have left, then is all normal
                    if len(df_current):
                        df_remain = df_current.copy()
                        add_remain(contracts, options, df_remain, df_stock, symbol)
                else:
                    # both right and others contract
                    df_double = df_current.query('others != "" & right != "100"')
                    df_current = add_contract(symbol, df_current, df_double, df_stock, contracts, options)

                    if len(df_current):
                        df_remain = df_current.copy()
                        add_remain(contracts, options, df_remain, df_stock, symbol)
                                                
            elif len(df_others):
                df_current = add_contract(symbol, df_current, df_others, df_stock, contracts, options)

                if len(df_current):
                    df_remain = df_current.copy()
                    add_remain(contracts, options, df_remain, df_stock, symbol)
            elif len(df_right):
                df_current = add_contract(symbol, df_current, df_right, df_stock, contracts, options)

                if len(df_current):
                    df_remain = df_current.copy()
                    add_remain(contracts, options, df_remain, df_stock, symbol)
            else:
                print df_current.to_string(line_width=1000)
                raise IndexError('Multi date but no other or split.')

        else:
            # all in one
            df_save = df_current.copy()
            contract = get_contract(df_save)
            contract['option_code'] = check_code(symbol, contract)
            df_save['option_code'] = contract['option_code']
            print output % (len(contracts), 'Append contract and option:', '%-16s %d' % (
                contract['option_code'], len(df_save)
            ))

            # basic valid option here
            df_save['valid'] = valid_option2(
                df_save.index, df_save['bid'], df_save['ask'],
                df_save['volume'], df_save['open_int'], df_save['dte']
            )
            df_save = df_save[df_save['valid'] == 1]
            del df_save['valid']

            # print df_save.to_string(line_width=1000)

            # set missing
            if len(df_save) > 1:
                latest = df_save['date'].iloc[0]
                oldest = df_save['date'].iloc[-1]
                length = np.sum((oldest <= df_stock.index) & (df_stock.index <= latest))
            else:
                length = 1

            contract['missing'] = length - len(df_save)

            contracts.append(contract)
            options.append(df_save)

    if len(contracts) and len(options):
        # merge all then save
        df_contract = pd.DataFrame(contracts)
        df_contract = df_contract.reset_index(drop=True)
        df_contract['ex_date'] = df_contract.apply(
            lambda x: pd.Timestamp(get_dte_date(x['ex_month'], int(x['ex_year']))), axis=1
        )
        df_contract['expire'] = df_contract['ex_date'] < last_date

        # print output % ('CLEAN', 'Validate Option Contract', '')
        # valid contract
        # df_contract['valid'] = valid_contract2(
        #     df_contract['ex_month'], df_contract['ex_year'], df_contract['right'], df_contract['special']
        # )
        # df_contract = df_contract.query('valid == 1')
        # del df_contract['valid']

        # make df_option
        df_option = pd.concat(options)
        """:type: pd.DataFrame"""
        df_option = df_option[[
            'ask', 'bid', 'date', 'delta', 'dte', 'extrinsic', 'gamma', 'impl_vol',
            'intrinsic', 'last', 'mark', 'open_int', 'option_code', 'prob_itm', 'prob_otm',
            'prob_touch', 'theo_price', 'theta', 'vega', 'volume'
        ]]
        df_option = df_option.set_index('date')

        # remove contract when no option
        empty_codes = np.setdiff1d(
            df_contract['option_code'], df_option['option_code'].unique()
        )
        df_contract = df_contract[~df_contract['option_code'].isin(empty_codes)]

        # remove duplicate contract (when option_code right, cycle date wrong)
        df_contract = df_contract.drop_duplicates('option_code')

        # print df_contract.dtypes
        # print df_option.dtypes
        # print df_contract.tail(10).to_string(line_width=1000)
        # print df_option.tail(10).to_string(line_width=1000)
        print output % (
            'TOTAL', 'df_contract: %d, df_option: %d' % (len(df_contract), len(df_option)), ''
        )

        # save into db
        db = pd.HDFStore('quote2.h5')
        for key in ('contract', 'data'):
            try:
                db.remove('option/%s/raw/%s' % (symbol.lower(), key))
            except KeyError:
                pass
        db.append('option/%s/raw/contract' % symbol, df_contract,
                  format='table', data_columns=True, min_itemsize=100)
        db.append('option/%s/raw/data' % symbol, df_option,
                  format='table', data_columns=True, min_itemsize=100)
        db.close()
        print output % ('SAVE', 'All data successful save into db', '')

    template = 'data/blank.html'
    parameters = dict(
        site_title='',
        title='',
    )

    return render(request, template, parameters)


