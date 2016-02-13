import logging
import os
import re
from fractions import Fraction

import pandas as pd
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from subprocess import Popen

from data.models import Underlying
from rivers.settings import QUOTE, CLEAN, BASE_DIR

logger = logging.getLogger('views')


def update_strike(df_split):
    """
    Update option_code strike with new strike
    :param df_split: pd.DataFrame
    :return: pd.DataFrame
    """
    df_change = df_split[df_split['right'].apply(lambda x: '/' in x)]

    df_change['strike'] = df_change.apply(
        lambda x: x['strike'] / Fraction(x['right']), axis=1
    )
    df_change['option_code'] = df_change.apply(
        lambda x: '%s%s' % (
            re.search('^([A-Z]+\d+[CP])[0-9]*\.?[0-9]*', x['option_code']).group(1),
            int(x['strike']) if int(x['strike']) == x['strike'] else x['strike']
        ), axis=1
    )

    df_split = df_split[~df_split.index.isin(df_change.index)]
    df_split = pd.concat([df_split, df_change])
    """:type: pd.DataFrame"""
    df_split['right'] = '100'

    return df_split


def merge_final(symbol):
    """
    Merge fillna normal, split/new, split/old into
    df_contract and df_option data
    :param symbol: str
    """
    symbol = symbol.lower()

    # get data
    df_list = {}
    db = pd.HDFStore(QUOTE)
    df_stock = db.select('stock/thinkback/%s' % symbol)
    db.close()
    last_date = df_stock.index[-1]

    db = pd.HDFStore(CLEAN)
    keys = ['normal', 'split/new', 'split/old']
    for key in keys:
        try:
            df_list[key] = db.select('option/%s/fillna/%s' % (symbol, key))
            logger.info('Get df_%s data length: %d' % (key, len(df_list[key])))
        except KeyError:
            pass
    db.close()

    # replace option_code in df_split/new
    if 'split/new' in df_list.keys():
        logger.info('Update df_split/new option_code')
        df_list['split/new']['option_code'] = df_list['split/new']['new_code']
        del df_list['split/new']['new_code']

    if 'split/old' in df_list.keys():
        logger.info('Update df_split/old option_code')
        df_list['split/old'] = update_strike(df_list['split/old'])

    df_all = pd.concat(df_list.values())
    """:type: pd.DataFrame"""
    logger.info('Merge all data length: %d' % len(df_all))
    df_all = df_all.sort_values(['date', 'option_code'])
    # print len(df_all)
    # get df_contract
    group = df_all.groupby('option_code')
    logger.info('Option_code length: %d' % len(group))
    index = [(key, value) for key, value in group['date'].max().iteritems()]
    df_index = df_all.set_index(['option_code', 'date'])
    df_contract = df_index[df_index.index.isin(index)]
    df_contract = df_contract[[
        'ex_date', 'ex_month', 'ex_year', 'name', 'others', 'right', 'special', 'strike'
    ]]
    df_contract = df_contract.reset_index()
    del df_contract['date']
    df_contract['expire'] = df_contract['ex_date'].apply(lambda x: x < last_date)
    # format df_option
    df_option = df_all[[
        'ask', 'bid', 'date', 'delta', 'dte', 'extrinsic',
        'gamma', 'impl_vol', 'intrinsic', 'last', 'mark', 'open_int', 'option_code',
        'prob_itm', 'prob_otm', 'prob_touch', 'theo_price', 'theta', 'vega', 'volume'
    ]]
    logger.info('Save df_contract, df_option into h5 db')
    db = pd.HDFStore(QUOTE)
    for key in ('contract', 'data'):
        try:
            db.remove('option/%s/final/%s' % (symbol, key))
        except KeyError:
            pass
    db.append('option/%s/final/contract' % symbol, df_contract,
              format='table', data_columns=True, min_itemsize=100)
    db.append('option/%s/final/data' % symbol, df_option,
              format='table', data_columns=True, min_itemsize=100)
    db.close()
    # update log
    underlying = Underlying.objects.get(symbol=symbol.upper())
    underlying.log += 'Merge final data: %s' % symbol.upper()
    underlying.log += 'df_contract length: %d' % len(df_contract)
    underlying.log += 'df_option length: %d' % len(df_option)
    underlying.enable = True
    underlying.save()


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

    db = pd.HDFStore(CLEAN)
    keys = db.keys()
    for key in keys:
        if symbol in key:
            logger.info('Remove data: %s' % key)
            db.remove(key)
    db.close()

    # make clean.h5 smaller size
    reshape_h5('clean.h5')

    # update log
    underlying = Underlying.objects.get(symbol=symbol.upper())
    underlying.log += 'All clean process data removed: %s' % symbol.upper()
    underlying.save()

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))


def reshape_h5(fname, dir_name=None):
    """
    Reshape the size of h5 db
    :param dir_name: str
    :param fname: str
    """
    os.chdir(dir_name if dir_name else BASE_DIR)
    p = Popen(r'ptrepack --chunkshape=auto %s temp.h5' % fname)
    p.communicate()  # wait complete
    os.remove(fname)
    os.rename('temp.h5', fname)


def import_option_h5(request, symbol):
    """
    Run all from import raw until fillna then merge
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start cli for prepare_raw: %s' % symbol)
    os.system("start cmd /k python data/manage.py import_option --symbol=%s" % symbol)

    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))
