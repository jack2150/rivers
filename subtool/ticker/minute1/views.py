import logging
import os
import pandas as pd
from django.shortcuts import render
from pandas.tseries.offsets import BDay

from base.ufunc import ds
from rivers.settings import QUOTE_DIR

logger = logging.getLogger('views')


def get_minute1_data(symbol, date):
    """

    :param symbol: str
    :param date: str
    :return: pd.DataFrame, pd.DataFrame
    """
    date = pd.to_datetime(date)

    path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
    db = pd.HDFStore(path)
    path = 'ticker/yahoo/minute1'
    df_minute1 = db.select(path).reset_index()
    db.close()

    dates = pd.to_datetime(df_minute1['dt'].dt.date.unique())
    start = dates[-1]
    stop = dates[-1] + BDay()
    if date in dates:
        # use match
        start = date
        stop = date + BDay()

    df_day = df_minute1[(df_minute1['dt'] >= start) & (df_minute1['dt'] <= stop)]

    return df_minute1, df_day


def minute1_si_report(request, symbol, date):
    """
    Report 1 minute simple indicator report
    :param request: request
    :param symbol: str
    :param date: str
    :return: render
    """
    df_minute1, df_day = get_minute1_data(symbol, date)



    logger.info('Ticker minute1 date: %s, length: %d' % (ds(date), len(df_day)))

    # start




    template = 'ticker/minute1/report.html'

    parameters = dict(
        site_title='Option time and sale summary',
        title='Option time and sale summary',
    )

    return render(request, template, parameters)
