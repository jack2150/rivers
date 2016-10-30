import logging
import os
import re
from time import sleep

import pandas as pd
from fractions import Fraction
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from subprocess import Popen, PIPE, STDOUT

from base.ufunc import ts
from data.models import Underlying
from rivers.settings import QUOTE_DIR, CLEAN_DIR, BASE_DIR, TEMP_DIR

logger = logging.getLogger('views')
output = '%-6s | %-30s'


def change_right(x):
    """
    Update right without '/'
    :param x: str
    :return:
    """
    r = 100 * Fraction(x)
    if r == round(r):
        r = '%d' % round(r)
    else:
        r = '%.2f' % r

    return r


def update_old_strike(df_split):
    """
    Update option_code strike with new strike for old_strike
    :param df_split: pd.DataFrame
    :return: pd.DataFrame
    """
    df_change = df_split.copy()
    # df_change = df_split[df_split['right'].apply(lambda x: '/' in x)].copy()
    # df_remain = df_split[~df_split.index.isin(df_change.index)]
    print output % ('UPDATE', 'old/split df_change: %d' % len(df_change))

    # change strike
    df_change['strike'] /= df_change['right'].apply(lambda x: Fraction(x)).astype('float')
    df_change = df_change.round({'strike': 2})
    print output % ('UPDATE', 'change old strike into new strike')

    # update option_code
    print output % ('UPDATE', 'change into new option_code')
    df_change['option_code'] = df_change[['option_code', 'strike']].apply(
        lambda x: '%s%s' % (
            re.search('^([A-Z]+\d+[CP])[0-9]*\.?[0-9]*', x['option_code']).group(1),
            int(x['strike']) if int(x['strike']) == x['strike'] else round(x['strike'], 2)
        ), axis=1
    )  # unable speed up

    # df_change['right'] = df_change['right'].apply(change_right)
    print output % ('UPDATE', 'set all right into 100')
    df_change['right'] = '100'

    # df_split = pd.concat([df_split, df_change])
    df_split = df_change.copy()
    print output % ('UPDATE', 'complete old/split new option_code and strike')

    return df_split


def merge_final(symbol):
    """
    Merge fillna normal, split/new, split/old into
    df_contract and df_option data
    :param symbol: str
    """
    print output % ('FINAL', 'merge all data into df_contract, df_option')
    symbol = symbol.lower()

    # get data
    df_list = {}
    path = os.path.join(QUOTE_DIR, '%s.h5' % symbol)
    db = pd.HDFStore(path)
    df_stock = db.select('stock/thinkback')
    db.close()
    last_date = df_stock.index[-1]

    path = os.path.join(CLEAN_DIR, '__%s__.h5' % symbol)
    db = pd.HDFStore(path)
    option_keys = ['normal', 'split/new', 'split/old']
    for key in option_keys:
        try:
            df_list[key] = db.select('option/fillna/%s' % key)
            print output % ('FINAL', 'Get df_%s data length: %d' % (key, len(df_list[key])))
        except KeyError:
            pass
    db.close()

    # replace option_code in df_split/new
    if 'split/new' in df_list.keys():
        print output % ('FINAL', 'Update df_split/new option_code')
        df_list['split/new']['option_code'] = df_list['split/new']['new_code']
        del df_list['split/new']['new_code']

    if 'split/old' in df_list.keys():
        print output % ('FINAL', 'Update df_split/old option_code')
        df_list['split/old'] = update_old_strike(df_list['split/old'])

    print output % ('MERGE', 'join df_normal, df_split old/new')
    df_all = pd.concat(df_list.values())
    """:type: pd.DataFrame"""

    print output % ('FINAL', 'Merge all data length: %d' % len(df_all))
    df_all = df_all.sort_values(['date', 'option_code'])

    # df_contract section
    df_contract = df_all[[
        'option_code', 'ex_date', 'name', 'others', 'right', 'special', 'strike'
    ]].copy()
    df_contract = df_contract.drop_duplicates(subset=['option_code'], keep='last')
    df_contract['expire'] = df_contract['ex_date'].apply(lambda x: x < last_date)
    df_contract = df_contract.reset_index(drop=True)
    print output % ('FINAL', 'df_contract length: %d' % len(df_contract))

    # format df_option
    option_keys = [
        'date', 'option_code', 'dte',
        'last', 'mark',
        'delta', 'gamma', 'theta', 'vega',
        'impl_vol', 'theo_price',
        'prob_itm', 'prob_otm', 'prob_touch',
        'volume', 'open_int',
        'extrinsic', 'intrinsic',
        'ask', 'bid',
    ]
    df_option = df_all[option_keys].copy()

    # format option
    for key in option_keys:
        if key not in ('date', 'dte', 'open_int', 'volume', 'option_code'):
            df_option[key] = df_option[key].astype('float')
        elif key in ('open_int', 'volume'):
            df_option[key] = df_option[key].astype('int')

    df_option = df_option.round({
        k: 2 for k in [
            'last', 'mark',
            'delta', 'gamma', 'theta', 'vega',
            'impl_vol', 'theo_price',
            'prob_itm', 'prob_otm', 'prob_touch',
            'extrinsic', 'intrinsic',
            'ask', 'bid'
        ]
    })

    print output % ('FINAL', 'Save df_contract, df_option into h5 db')

    db = pd.HDFStore(os.path.join(QUOTE_DIR, '%s.h5' % symbol))
    try:
        db.remove('option')
    except KeyError:
        pass

    db.append('option/contract', df_contract,
              format='table', data_columns=True)
    db.append('option/data', df_option,
              format='table', data_columns=True, min_itemsize=100)
    db.close()

    underlying = Underlying.objects.get(symbol=symbol.upper())
    underlying.enable = True
    underlying.save()

    # update log
    Underlying.write_log(symbol, [
        'Final df_contract: %d' % len(df_contract),
        'Final df_option: %d' % len(df_option),
        '%s stock & option quote created' % symbol.upper()
    ])


def merge_final_h5(request, symbol):
    """
    Get all data from db then merge into df_contract, df_option
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start merge all data: %s' % symbol.upper())
    merge_final(symbol)

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))


def remove_clean_h5(request, symbol):
    """
    Remove raw, valid, clean, fillna data from db to save space
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start remove process data: %s' % symbol.upper())

    symbol = symbol.lower()

    path = os.path.join(CLEAN_DIR, '__%s__.h5' % symbol)
    os.remove(path)

    # make clean.h5 smaller size
    # reshape_h5('clean.h5')

    # update log
    Underlying.write_log(symbol, ['All clean process data removed: %s' % symbol.upper()])

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))


def reshape_h5(fname, dir_name=None):
    """
    Reshape the size of h5 db
    :param dir_name: str
    :param fname: str
    """
    sleep(1)

    try:
        os.chdir(dir_name if dir_name else BASE_DIR)
        temp = 'temp.h5'
        p = Popen(r'ptrepack --chunkshape=auto %s %s' % (fname, temp))
        p.communicate()  # wait complete
        os.remove(fname)
        os.rename(temp, fname)
    except WindowsError:
        pass


def import_option_h5(request, symbol):
    """
    Run all from import raw until fillna then merge
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start cli for prepare_raw: %s' % symbol)
    # os.system("start cmd /k python data/manage.py import_option --symbol=%s" % symbol)
    cmd = "start cmd /k python data/manage.py import_option --symbol=%s" % symbol
    Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)  # no wait

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))


def import_weekday_h5(request, symbol):
    """
    Run all from import raw until fillna then merge
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start cli for prepare_raw: %s' % symbol)
    os.system("start cmd /k python data/manage.py import_weekday --symbol=%s" % symbol)

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))