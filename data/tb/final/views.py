import logging
import pandas as pd
from django.core.urlresolvers import reverse
from django.shortcuts import redirect

from rivers.settings import QUOTE

logger = logging.getLogger('views')


def merge_option_h5(request, symbol):
    """
    Get all data from db then merge into df_contract, df_option
    :param request: request
    :param symbol: str
    :return: render
    """
    logger.info('Start merge all data: %s' % symbol.upper())
    symbol = symbol.lower()

    # get data
    df_list = []
    keys = ['normal', 'split/new', 'split/old']
    db = pd.HDFStore(QUOTE)
    for key in keys:
        df_list.append(db.select('option/%s/clean/%s' % (symbol, key)))
    db.close()

    # merge all
    df_all = pd.concat(df_list)

    # make df_contract, df_option



    # format columns

    # todo: later, after fillna




    return redirect(reverse('admin:manage_underlying', kwargs={'symbol': symbol}))