import logging
import os
import numpy as np
import pandas as pd
from glob import glob
from data.tb.thinkback import ThinkBack
from data.models import Underlying
from data.skip_days import holiday, offday
from rivers.settings import QUOTE_DIR, THINKBACK_DIR

logger = logging.getLogger('views')


def extract_stock(symbol):
    """
    Import csv files stock data only
    :param symbol: str
    """
    print '=' * 60
    print '%-6s | %-30s %s' % ('IMPORT', 'Import df_stock:', symbol.upper())
    print '=' * 60

    symbol = symbol.lower()

    # get underlying
    underlying = Underlying.objects.get(symbol=symbol.upper())
    start = underlying.start_date
    end = underlying.stop_date

    # move files into year folder
    # noinspection PyUnresolvedReferences
    path = os.path.join(THINKBACK_DIR, symbol)
    logger.info('open thinkback path: %s' % path)
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
            print '%-6s | %-30s' % (i, 'Read %s' % os.path.basename(f))
            stock_data = ThinkBack(f).get_stock()

            try:
                if int(stock_data['volume']) == 0:
                    error_dates.append(fdate)
                    continue  # skip this part

                if float(stock_data['last']) <= 0:  # skip if not close price
                    continue
            except ValueError:
                continue

            # append into stock list
            stocks['date'].append(pd.to_datetime(stock_data['date']))
            stocks['open'].append(float(stock_data['open']))
            stocks['high'].append(float(stock_data['high']))
            stocks['low'].append(float(stock_data['low']))
            stocks['close'].append(float(stock_data['last']))
            stocks['volume'].append(int(stock_data['volume']))

    # start save
    df_stock = pd.DataFrame(stocks)
    df_stock = df_stock.round({
        'open': 2,
        'high': 2,
        'low': 2,
        'close': 2,
    })

    if len(df_stock):
        # check duplicate date
        dates = df_stock['date']
        dup = dates[dates.duplicated()]
        if len(dup):
            print 'duplicate date:'
            print dup
            raise LookupError('Duplicate rate in df_stock index')

        df_stock = df_stock.set_index('date')
        path = os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower())
        logger.info('Save thinkback stock, path: %s' % path)
        db = pd.HDFStore(path)
        try:
            db.remove('stock/thinkback')
        except KeyError:
            pass
        db.append('stock/thinkback', df_stock, format='table', data_columns=True)
        db.close()

    missing = list()
    bdays = pd.bdate_range(start=start, end=end, freq='B')
    for bday in bdays:
        if holiday(bday.date()) or offday(bday.date()):
            continue

        if bday not in df_stock.index:
            missing.append(bday.strftime('%m/%d/%Y'))

    # update underlying
    underlying.missing = '\n'.join(missing)
    underlying.log += 'Thinkback stock imported, symbol: %s length: %d \n' % (
        symbol.upper(), len(df_stock)
    )
    underlying.log += 'df_stock length: %d missing dates: %d\n' % (len(df_stock), len(missing))
    underlying.save()

    print '=' * 60
    print '%-6s | %-30s %s' % ('IMPORT', 'Complete import df_stock:', symbol.upper())
    print '=' * 60

