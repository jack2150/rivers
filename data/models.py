import pandas as pd
from django.db import models
from rivers.settings import QUOTE


class Underlying(models.Model):
    symbol = models.CharField(max_length=20, unique=True)

    start_date = models.DateField(default='2009-01-01')
    stop_date = models.DateField(null=True, blank=True)

    option = models.BooleanField(default=False)  # got option or not
    final = models.BooleanField(default=False)  # ready to use or not
    enable = models.BooleanField(default=False)  # use or not use

    missing = models.TextField(default='', blank=True)  # all missing dates
    log = models.TextField(default='', blank=True)  # use for all process

    class Meta:
        ordering = ['symbol']

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

        db = pd.HDFStore(QUOTE)
        if len(query):
            df_stock = db.select('stock/%s/%s' % (source, self.symbol.lower()), query)
        else:
            df_stock = db.select('stock/%s/%s' % (source, self.symbol.lower()))

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
        db = pd.HDFStore(QUOTE)
        for source in ('google', 'yahoo'):
            try:
                df_stock = db.select(
                    'stock/%s/%s' % (source, symbol.lower()),
                    "index == Timestamp('%s')" % date.strftime('%Y%m%d')
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
        db = pd.HDFStore(QUOTE)
        df_contract = db.select('option/%s/final/contract' % self.symbol.lower())
        df_option = db.select('option/%s/final/data' % self.symbol.lower())
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
        max_length=20, help_text='Example: 3 for 2 is 2/3'
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
        db = pd.HDFStore(QUOTE)
        try:
            df_rate = db.select('treasury/RIFLGFCY01_N_B')
        except KeyError:
            raise LookupError('Treasury not import yet')

        db.close()

        return df_rate['rate']

    def __unicode__(self):
        return '{time_period}'.format(
            time_period=self.time_period
        )
