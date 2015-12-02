import os

import re
from django.shortcuts import render
from data.plugin.csv.views import get_exist_stocks, get_dte_date
from data.plugin.thinkback import ThinkBack
from rivers.settings import BASE_DIR
import numpy as np
import pandas as pd


def make_code2(symbol, others, right, special, ex_date, name, strike):
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
    extra = ''
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
    output = '%-6s | %-30s %s'
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

    df_option = pd.DataFrame(options)
    df_option['date'] = pd.to_datetime(df_option['date'])
    print df_option.head().to_string(line_width=1000)

    db = pd.HDFStore('test.h5')
    for key in ('option', 'tkeys'):
        try:
            db.remove(key)
        except KeyError:
            pass
    db.append('option', df_option)
    db.append('tkeys', pd.Series(keys))
    db.close()

    exit()
    """

    db = pd.HDFStore('test.h5')
    df_all = db.select('option')
    """:type: pd.DataFrame"""
    df_all = df_all.sort_values('date', ascending=False)
    keys = db.select('tkeys')
    db.close()

    #df_test = df_all.query('option_code == "AIG140517C49"') # normal
    #df_test = df_all.query('option_code == "UZLAT" | option_code == "AILAT"')  # split
    #df_test = df_all.query('option_code == "AIG2110219C52.5" | option_code == "AIG110219C52.5"')  # add others
    #df_test = df_all.query('option_code == "AJU100220C110" | option_code == "IKG100320C33"')  # wrong symbol
    df_test = df_all[df_all['option_code'].isin(["ZEU110122C2.5", "VAFAZ", "ZEUAZ"])]  # code change + others/split
    panel = [df_test]
    #print df_all.to_string(line_width=1000)


    # print df_all.head().to_string(line_width=1000)
    #print keys

    """
    panel = []
    size = 100
    start = 16000
    end = 17000
    #for i in range(0, len(keys), size):
    for i in range(start, end, size):
        print i
        df_size = df_all.query('%r <= key < %r' % (i, i + size))
        for j, k in enumerate(keys[i:i + size], start=i):
            df_current = df_size.query('key == %r' % j)
            print output % (j, 'Get df_current from df_all:', '%-16s %d' % (k, len(df_current)))
            if len(df_current):
                panel.append(df_current)
    """

    count = 0
    contracts = []
    options = []
    # start matching
    for key, df_current in enumerate(panel):
        #print df_current.head().to_string(line_width=1000)

        special_codes = []
        normal_codes = []
        for code in df_current['option_code'].unique():
            contract = df_current.query('option_code == %r' % code).iloc[0][[
                'ex_month', 'ex_year', 'name', 'option_code',
                'others', 'right', 'special', 'strike'
            ]]

            if len(contract['others']) or '/' in contract['right']:
                special_codes.append((code, contract))
            else:
                normal_codes.append((code, contract))

        codes = special_codes + normal_codes
        for code, contract in codes:
            df_temp = df_current.query('option_code == %r' % code).copy()
            if len(df_temp) == 0:
                continue

            print output % (count, 'Append contract and option:', '%-16s %d' % (code, len(df_temp)))
            count += 1
            oldest = df_temp['date'].iloc[-1]

            # for others and split
            if len(contract['others']) or '/' in contract['right']:
                df_before = df_current.query('date < %r' % oldest)
                if len(df_before) != len(df_before['date'].unique()):
                    df_before = df_before.query('others == %r & right == %r' % (
                        contract['others'], contract['right']
                    ))

                df_temp = pd.concat([df_temp, df_before])
                """:type: pd.DataFrame"""
                df_current = df_current[~df_current.index.isin(df_temp.index)]
                #print df_temp.to_string(line_width=1000)

            # make sure date is unique
            if len(df_temp) != len(df_temp['date'].unique()):
                print df_temp.to_string(line_width=1000)
                raise IndexError('Invalid unique date on df_temp: %d %d' % (
                    len(df_temp), len(df_temp['date'].unique())
                ))

            # because contract column is going delete in df_option, so no update require
            # update contract option_code
            if len(code) < 9 or symbol.upper() not in code:  # old format or no symbol
                ex_date = pd.Timestamp(get_dte_date(contract['ex_month'], int(contract['ex_year'])))

                new_code = make_code2(
                    symbol, contract['others'], contract['right'], contract['special'],
                    ex_date, contract['name'], contract['strike']
                )
                print output % ('CODE', 'Update (old format):', '%-16s -> %-16s' % (
                    contract['option_code'], new_code
                ))
                contract['option_code'] = new_code

            # only update option_code
            df_temp['option_code'] = contract['option_code']
            #print contract
            #print df_temp.to_string(line_width=1000)

            contracts.append(contract)
            options.append(df_temp)

    if len(contracts) and len(options):
        df_contract = pd.DataFrame(contracts)
        df_contract['ex_date'] = df_contract.apply(
            lambda x: pd.Timestamp(get_dte_date(x['ex_month'], int(x['ex_year']))), axis=1
        )
        df_contract['expire'] = df_contract['ex_date'] < last_date

        df_option = pd.concat(options)
        """:type: pd.DataFrame"""
        """
        df_option = df_option[[
            'ask', 'bid', 'date', 'delta', 'dte', 'extrinsic', 'gamma', 'impl_vol',
            'intrinsic', 'last', 'mark', 'open_int', 'option_code', 'prob_itm', 'prob_otm',
            'prob_touch', 'theo_price', 'theta', 'vega', 'volume'
        ]]
        """

        print df_contract.tail(10).to_string(line_width=1000)
        #print df_option.tail(10).to_string(line_width=1000)
        print df_option.to_string(line_width=1000)
        print len(df_contract), len(df_option)
    # todo: valid

    template = 'data/blank.html'
    parameters = dict(
        site_title='',
        title='',
    )

    return render(request, template, parameters)
