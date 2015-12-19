from django.shortcuts import redirect
from numba import jit

from data.plugin.csv import get_exist_stocks
from data.plugin.raw import read_file, output, get_contract
import numpy as np
import pandas as pd

from rivers.settings import QUOTE


def csv_raw_option(symbol):
    """
    :param symbol: str
    :return: render
    """
    symbol = symbol.lower()

    df_stock = get_exist_stocks(symbol).sort_index(ascending=False)

    keys, options = read_file(df_stock, symbol)

    # make all options df
    df_all = pd.DataFrame(options)
    df_all['date'] = pd.to_datetime(df_all['date'])

    db = pd.HDFStore(QUOTE)
    db.append('test/%s/raw/data' % symbol, df_all)
    db.close()


def merge_raw_option(symbol):
    """
    :param symbol: str
    :return: render
    """
    symbol = symbol.lower()

    db = pd.HDFStore(QUOTE)
    df_all = db.select('test/%s/raw/data' % symbol)
    db.close()
    #print df_all.head().to_string(line_width=1000)

    # df_all = df_all[:100]
    df_all['id'] = df_all.apply(
        lambda c: '%s%s%s%sR%sO%s' % (
            c['ex_month'], c['ex_year'], c['name'], c['strike'], c['right'], c['others']
        ),
        axis=1
    )
    # print df_all.to_string(line_width=1000)

    normal = []
    right = []
    others = []
    for i, id in enumerate(df_all['id'].unique()):
        print i, id,
        df = df_all[df_all['id'] == id]

        c = get_contract(df)

        if len(c['others']):
            print 'others'
            others.append(df)
        elif c['right'] != '100' and c['special'] != 'Mini':
            print 'right'
            right.append(df)
        else:
            print 'normal'
            normal.append(df)

    db = pd.HDFStore(QUOTE)
    if len(normal):
        df_normal = pd.concat(normal)
        db.remove('test/%s/raw/normal' % symbol)
        db.append('test/%s/raw/normal' % symbol, df_normal)

    if len(right):
        df_right = pd.concat(right)
        db.remove('test/%s/raw/right' % symbol)
        db.append('test/%s/raw/right' % symbol, df_right)

    if len(others):
        df_others = pd.concat(others)
        db.remove('test/%s/raw/others' % symbol)
        db.append('test/%s/raw/others' % symbol, df_others)
    db.close()


def merge_option_others(symbol):
    """
    Others is always old format, new format got no others or right
    :param symbol: str
    """
    db = pd.HDFStore(QUOTE)
    df_others = db.select('test/%s/raw/others' % symbol)
    df_normal = db.select('test/%s/raw/normal' % symbol)
    db.close()

    print 'df_others length: %d' % len(df_others)
    print 'df_normal length: %d' % len(df_normal)

    # codes = df_others['option_code'].unique()

    group = df_others.groupby('id')
    df_code = pd.DataFrame({'start': group['date'].min(), 'stop': group['date'].max()})
    df_code = df_code.sort_values('stop', ascending=False)
    # print df_code.to_string(line_width=1000)

    data = []
    for id2, date in df_code.iterrows():
        print output % ('START', 'id: %s ' % id2, 'from: %s to: %s' % (
            date['start'].strftime('%Y-%m-%d'), date['stop'].strftime('%Y-%m-%d')
        ))
        df_current = df_others[df_others['id'] == id2]

        if len(df_current) == 0:
            print output % ('EMPTY', 'No more others data (added)', '')
            continue

        c = get_contract(df_current)
        oldest = df_current['date'].iloc[-1]
        index = df_current['index'].iloc[0]
        code = df_current['option_code'].iloc[0]
        right = df_current['right'].iloc[0]

        print output % ('OTHERS', 'Get others row using', '')
        # print df_current.to_string(line_width=1000)

        # find others before, others is not split so strike is always same
        df_continue = df_others.query('index == %r & date < %r' % (index, oldest))
        # print df_continue.to_string(line_width=1000)
        while len(df_continue):
            # check duplicate
            if len(df_continue) != len(df_continue['date'].unique()):
                print output % ('OTHERS', 'Duplicate date in others continue data', '')
                for key, value in [('option_code', code), ('right', right)]:
                    df_similar = df_continue[df_continue[key] == value]

                    if len(df_similar):
                        print output % ('OTHERS', 'Found others continue data using',
                                        '%s: %s' % (key, value))
                        df_current = pd.concat([df_current, df_similar])
                        break
                else:
                    # no break, loop until end
                    print output % ('OTHERS', 'Found pass data but have duplicate date', '')
                    df_continue = pd.DataFrame(columns=['index', 'date'])
            else:
                print output % ('OTHERS', 'Merge others continue option data', len(df_continue))
                df_current = pd.concat([df_current, df_continue])

            oldest = df_current['date'].iloc[-1]
            df_continue = df_continue.query('index == %r & date < %r' % (index, oldest))
            # print df_current.to_string(line_width=1000)
        else:
            # remove data in df_others
            print output % ('REMOVE', 'Added others continue data', 'old data removed')
            df_others = df_others[~df_others.index.isin(df_current.index)]

        # find normal before
        print output % ('OTHERS', 'Get normal row using', 'index: %s' % index)
        df_continue = df_normal.query('index == %r & date < %r' % (index, oldest))
        # print df_continue.to_string(line_width=1000)
        if len(df_continue) == len(df_continue['date'].unique()):
            print output % ('OTHERS', 'Merge normal continue option data', len(df_continue))
            df_current = pd.concat([df_current, df_continue])

            # remove data in df_normal
            df_normal = df_normal[~df_normal.index.isin(df_continue.index)]
        else:
            print output % ('OTHERS', 'Found normal but duplicate date', len(df_continue))

        # done, append into data
        data.append(df_current)
        print '-' * 100
        # print df_current.to_string(line_width=1000)

    print 'df_others length: %d' % len(df_others)
    print 'df_normal length: %d' % len(df_normal)
    print len(data)

    db = pd.HDFStore(QUOTE)
    db.append('test/%s/data/others' % symbol.lower(), pd.concat(data))
    db.close()





"""
old format
1. merge option others, date1 to date0, remove normal
2. merge option split, date1 to date0, remove normal
3. merge option normal, check is split or special dividend
"""





















