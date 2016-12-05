import logging
import os
import urllib2
from StringIO import StringIO
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, HttpResponse
import pandas as pd
from pandas.tseries.offsets import Minute, Hour
from base.ufunc import ts, ds
from rivers.settings import QUOTE_DIR

logger = logging.getLogger('views')
MINUTE_URL = 'https://www.google.com/finance/getprices?i=60&p=15d&f=d,o,h,l,c,v&df=cpct&q=%s'

# http://chartapi.finance.yahoo.com/instrument/1.0/GOOG/chartdata;type=quote;range=15d/csv
# google max 15 days, yahoo not complete
# store in ticker/yahoo/minute1, without duplicate


def web_yahoo_minute_data(request, symbol):
    """
    Download yahoo minute data then save into db
    :param request: request
    :param symbol: symbol
    :return: redirect
    """
    response = urllib2.urlopen(MINUTE_URL % symbol.upper())
    lines = response.readlines()

    start = [i for i, k in enumerate(lines) if 'TIMEZONE_OFFSET=-300' in k].pop() + 1
    stop = len(lines)

    df_minute = pd.read_csv(StringIO(''.join(lines[start:stop])), header=None)
    # Timestamp,close,high,low,open,volume
    df_minute.columns = ['dt', 'close', 'high', 'low', 'open', 'volume']

    df_list = []
    row_ts = [(i, d[1:]) for i, d in enumerate(df_minute['dt']) if 'a' in d]
    row_ts.append((len(df_minute), ''))  # for latest
    for (i, date), (j, _) in zip(row_ts[:-1], row_ts[1:]):
        start_time = pd.to_datetime(date, unit='s')
        reduce_hour = start_time.hour - 9  # convert to correct time

        df = df_minute[i:j].copy()
        df.loc[df.index[0], 'dt'] = 0
        df['dt'] = df['dt'].apply(lambda x: start_time + Minute(x) - Hour(reduce_hour))
        df = df[['dt', 'open', 'high', 'low', 'close', 'volume']]
        df = df.round(2)
        # ts(pd.concat([df.head(10), df.tail(10)]))

        df_list.append(df)

    df_all = pd.concat(df_list)
    """:type: pd.DataFrame"""
    df_all = df_all.set_index('dt')
    # ts(df_all.head())

    dates = df_all.index.unique()
    logger.info('date: %s to %s' % (ds(dates[0]), ds(dates[-1])))

    path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
    db = pd.HDFStore(path)
    try:
        df_minute = db.select('ticker/yahoo/minute1')
        if len(df_minute):
            try:
                db.remove(
                    'ticker/yahoo/minute1',
                    where='index >= Timestamp("%s")' % dates[0].strftime('%Y%m%d')
                )
            except NotImplementedError:
                db.remove('ticker/yahoo/minute1')
    except (KeyError, TypeError):
        pass

    db.append('ticker/yahoo/minute1', df_all)
    db.close()

    logger.info('Save df_minute data length: %s, path: %s' % (len(df_all), path))

    return HttpResponse('not yet')
