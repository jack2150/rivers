import os

import pandas as pd
from datetime import datetime
from django.db import models
from rivers.settings import QUOTE_DIR, TREASURY_DIR


class Underlying(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    google_symbol = models.CharField(max_length=100, blank=True, default='')
    yahoo_symbol = models.CharField(max_length=100, blank=True, default='')

    # basic detail
    sector = models.CharField(max_length=20, default='', blank=True)
    industry = models.CharField(max_length=100, default='', blank=True)
    exchange = models.CharField(max_length=20, default='', blank=True)
    market_cap = models.CharField(
        max_length=20, default='large',
        choices=(
            ('mega', '200B or more'), ('large', '10B to 200B'), ('mid', '2B to 10B'),
            ('small', '300M to 2B'), ('micro', '50M to 300M'), ('nano', 'less than 50M')
        )
    )
    country = models.CharField(max_length=50, default='', blank=True)

    # other detail
    activity = models.CharField(
        max_length=20, default='moderately',
        choices=(
            ('highly', 'Highly Followed'), ('moderately', 'Moderately Followed'),
            ('neglected', 'Neglected')
        )
    )
    classify = models.CharField(
        max_length=20, default='normal',
        choices=(
            ('growth', 'Growth Stock'), ('value', 'Value Stock'),
            ('dividend', 'Dividend Stock'), ('normal', 'Normal Stock')
        )
    )

    # data detail
    start_date = models.DateField(default='2009-01-01')
    stop_date = models.DateField(null=True, blank=True)

    company = models.CharField(max_length=200, default='', blank=True)  # company name
    optionable = models.BooleanField(default=True)  # got option or not
    shortable = models.BooleanField(default=True)  # can short or not
    final = models.BooleanField(default=False)  # ready to use or not
    enable = models.BooleanField(default=False)  # use or not use

    missing = models.TextField(default='', blank=True)  # all missing dates
    log = models.TextField(default='', blank=True)  # use for all process

    class Meta:
        ordering = ['symbol']

    @staticmethod
    def write_log(symbol, lines, missing=[]):
        """
        Write log into underlying
        :param symbol: str
        :param lines: list
        :param missing: list
        :return:
        """
        underlying = Underlying.objects.get(symbol=symbol.upper())

        data = []
        for line in lines:
            log = '%s: %s' % (datetime.today().strftime('%Y-%m-%d %H:%M:%S'), line)
            data.append(log)

        data.append('-' * 60 + '\n')
        underlying.log += '\n'.join(data)

        if len(missing):
            underlying.missing = '\n'.join(missing)
        else:
            underlying.missing = ''

        underlying.save()

    def get_stock(self, source, start, stop):
        """
        Get stock dataframe for google source
        :param start: date
        :param stop: date
        :param source: str ('thinkback', 'google', 'yahoo')
        :return: DataFrame
        """
        if type(start) in (str, unicode):
            start = pd.datetime.strptime(start, '%Y-%m-%d')

        if type(stop) in (str, unicode):
            stop = pd.datetime.strptime(stop, '%Y-%m-%d')

        if start and stop:
            query = "index >= Timestamp('%s') & index <= Timestamp('%s')" % (
                start.strftime('%Y%m%d'), stop.strftime('%Y%m%d')
            )
        elif start:
            query = "index >= Timestamp('%s')" % start.strftime('%Y%m%d')
        elif stop:
            query = "index <= Timestamp('%s')" % stop.strftime('%Y%m%d')
        else:
            query = ''

        db = pd.HDFStore(os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower()))
        if len(query):
            df_stock = db.select('stock/%s' % source, query)
        else:
            df_stock = db.select('stock/%s' % source, query)
        db.close()
        df_stock['symbol'] = self.symbol.upper()

        return df_stock.reset_index()

    @staticmethod
    def get_price(symbol, date):
        """
        Get price for single symbol and single date
        :param symbol: str
        :param date: date
        :return: dict
        """
        if type(date) in (str, unicode):
            date = pd.datetime.strptime(date, '%Y-%m-%d')

        data = None
        df_stock = pd.DataFrame()
        db = pd.HDFStore(os.path.join(QUOTE_DIR, '%s.h5' % symbol.lower()))
        for source in ('google', 'yahoo'):
            try:
                df_stock = db.select(
                    'stock/%s' % source, "index == Timestamp('%s')" % date.strftime('%Y%m%d')
                )
            except KeyError:
                pass

            if len(df_stock):
                data = dict(df_stock.ix[df_stock.index[0]])

                for key in data.keys():
                    if key != 'volume':
                        data[key] = float(data[key])

                break
        db.close()

        return data

    def get_option(self):
        """
        Get underlying option
        :return: DataFrame, DataFrame
        """
        db = pd.HDFStore(os.path.join(QUOTE_DIR, '%s.h5' % self.symbol.lower()))
        df_contract = db.select('option/contract')
        df_option = db.select('option/data')
        db.close()

        return df_contract, df_option

    def __unicode__(self):
        return '{symbol}'.format(
            symbol=self.symbol
        )


class SplitHistory(models.Model):
    symbol = models.CharField(max_length=20)
    date = models.DateField()
    fraction = models.CharField(
        max_length=20, help_text='Example: 2 for 3 is 2/3'
    )

    def __unicode__(self):
        return '{symbol} {date} {fraction}'.format(
            symbol=self.symbol, date=self.date, fraction=self.fraction
        )


class Treasury(models.Model):
    """
    "Series Description","Market yield on U.S. Treasury securities at 1-year
    constant maturity, quoted on investment basis"
    "Unit:","Percent:_Per_Year"
    "Multiplier:","1"
    "Currency:","NA"
    "Unique Identifier: ","H15/H15/RIFLGFCY01_N.B"
    "Time Period","RIFLGFCY01_N.B"
    """
    start_date = models.DateField()
    stop_date = models.DateField()

    series_description = models.TextField()
    unit = models.CharField(max_length=100)
    multiplier = models.FloatField()
    currency = models.CharField(max_length=20)
    unique_identifier = models.CharField(max_length=100)
    time_period = models.CharField(max_length=100)

    def to_key(self):
        """
        use when open hdf5 key
        :return: str
        """
        return self.time_period.replace('.', '_')

    @staticmethod
    def get_rf():
        """
        Get risk free dataframe
        :return: DataFrame
        """
        db = pd.HDFStore(TREASURY_DIR)
        try:
            df_rate = db.select('RIFLGFCY01_N_B')
        except KeyError:
            raise LookupError('Treasury not import yet')

        db.close()

        return df_rate['rate']

    def __unicode__(self):
        return '{time_period}'.format(
            time_period=self.time_period
        )
