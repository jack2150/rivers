from django.db import models
import pandas as pd
from pandas.util.testing import DataFrame, Series


class Underlying(models.Model):
    symbol = models.CharField(max_length=20, unique=True)

    start = models.DateField(default='2009-01-01')
    stop = models.DateField(default=pd.datetime.today())

    thinkback = models.IntegerField(default=0)
    google = models.IntegerField(default=0)
    yahoo = models.IntegerField(default=0)

    def __unicode__(self):
        return '{symbol} {stop}'.format(
            symbol=self.symbol,
            start=self.start,
            stop=self.stop
        )


class Stock(models.Model):
    symbol = models.CharField(max_length=20)
    
    date = models.DateField()
    open = models.DecimalField(max_digits=10, decimal_places=2)
    high = models.DecimalField(max_digits=10, decimal_places=2)
    low = models.DecimalField(max_digits=10, decimal_places=2)
    close = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()

    source = models.CharField(max_length=10)
    unique_together = (('symbol', 'date', 'source', 'underlying'),)

    def load_dict(self, values):
        """
        Save dict data item into field
        :param values: dict
        :return: Stock
        """
        self.date = values['date']
        self.open = round(float(values['open']), 2)
        self.high = round(float(values['high']), 2)
        self.low = round(float(values['low']), 2)
        self.close = round(float(values['close'] if 'close' in values.keys() else values['last']), 2)
        self.volume = long(values['volume'])

        return self

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.open, self.high, self.low, self.close, self.volume]],
            index=[self.date],
            columns=['Open', 'High', 'Low', 'Close', 'Volume']
        )

    def __unicode__(self):
        return '{symbol} {date} {open} {high} {low} {close} {volume}'.format(
            symbol=self.symbol,
            date=self.date,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume
        )


class OptionContract(models.Model):
    """
    Tos option contract only
    """
    symbol = models.CharField(max_length=20)

    ex_month = models.CharField(max_length=4)
    ex_year = models.IntegerField(max_length=2)
    right = models.CharField(max_length=20)
    special = models.CharField(max_length=10)
    strike = models.DecimalField(max_length=4, max_digits=10, decimal_places=2)
    contract = models.CharField(max_length=4)
    option_code = models.CharField(max_length=200, unique=True)
    others = models.CharField(max_length=200, default='', blank='')

    source = models.CharField(max_length=20)

    def load_dict(self, values):
        """
        Set stock dict into model field
        :param values: dict
        """
        self.ex_month = values['ex_month']
        self.ex_year = values['ex_year']
        self.right = values['right']
        self.special = values['special']
        self.strike = values['strike']
        self.contract = values['contract']
        self.option_code = values['option_code']
        self.others = values['others']

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.right, self.special, self.ex_month, self.ex_year,
                   self.strike, self.contract, self.others]],
            index=[self.option_code],
            columns=['Right', 'Special', 'Ex_Month', 'Ex_Year', 'Strike', 'Contract', 'Others']
        )

    def __unicode__(self):
        """
        Output explain this model
        """
        return '{right} {special} {ex_month} {ex_year} {strike} {contract}{others}'.format(
            right=self.right,
            special=self.special,
            ex_month=self.ex_month,
            ex_year=self.ex_year,
            strike=self.strike,
            contract=self.contract,
            others=' (%s)' % self.others if self.others else ''
        )


class Option(models.Model):
    """
    Tos option contract price only
    """
    option_contract = models.ForeignKey(OptionContract)

    date = models.DateField()
    dte = models.IntegerField(max_length=5)

    bid = models.DecimalField(max_digits=10, decimal_places=2)
    ask = models.DecimalField(max_digits=10, decimal_places=2)
    last = models.DecimalField(max_digits=10, decimal_places=2)
    mark = models.DecimalField(max_digits=10, decimal_places=2)

    delta = models.DecimalField(max_digits=10, decimal_places=2)
    gamma = models.DecimalField(max_digits=10, decimal_places=2)
    theta = models.DecimalField(max_digits=10, decimal_places=2)
    vega = models.DecimalField(max_digits=10, decimal_places=2)

    theo_price = models.DecimalField(max_digits=10, decimal_places=2)
    impl_vol = models.DecimalField(max_digits=10, decimal_places=2)

    prob_itm = models.DecimalField(max_digits=10, decimal_places=2)
    prob_otm = models.DecimalField(max_digits=10, decimal_places=2)
    prob_touch = models.DecimalField(max_digits=10, decimal_places=2)

    volume = models.IntegerField()
    open_int = models.IntegerField()

    intrinsic = models.DecimalField(max_digits=10, decimal_places=2)
    extrinsic = models.DecimalField(max_digits=10, decimal_places=2)

    unique_together = (('option_contract', 'date'),)

    def load_dict(self, values):
        """
        Set stock dict into model field
        :param values: dict
        """
        self.date = values['date']
        self.dte = values['dte']
        self.bid = values['bid']
        self.ask = values['ask']
        self.mark = values['mark']
        self.last = values['last']
        self.delta = values['delta']
        self.gamma = values['gamma']
        self.vega = values['vega']
        self.theta = values['theta']
        self.theo_price = values['theo_price']
        self.impl_vol = values['impl_vol']
        self.prob_itm = values['prob_itm']
        self.prob_otm = values['prob_otm']
        self.prob_touch = values['prob_touch']
        self.volume = values['volume']
        self.open_int = values['open_int']
        self.intrinsic = values['intrinsic']
        self.extrinsic = values['extrinsic']

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.dte, self.bid, self.ask, self.mark, self.last,
                   self.delta, self.gamma, self.vega, self.theta,
                   self.theo_price, self.impl_vol,
                   self.prob_itm, self.prob_otm, self.prob_touch,
                   self.volume, self.open_int, self.intrinsic, self.extrinsic]],
            index=[[self.option_contract.option_code], [self.date]],
            columns=['DTE', 'Bid', 'Ask', 'Mark', 'Last',
                     'Delta', 'Gamma', 'Vega', 'Theta',
                     'Theo Price', 'Impl Vol',
                     'Prob ITM', 'Prob OTM', 'Prob Touch',
                     'Volume', 'Open Int', 'Intrinsic', 'Extrinsic']
        )

    def __unicode__(self):
        """
        Output explain this model
        """
        return '{date} {option_contract}'.format(
            date=self.date,
            option_contract=self.option_contract
        )    


class Dividend(models.Model):
    """
    Symbol,Div. Amount,Div. Announced Date,Ex Div. Date,Div. Record Date,Div. Payable Date
    AAN,$0.021,11/7/13,11/27/13,12/2/13,1/3/14
    """
    symbol = models.CharField(max_length=20)
    amount = models.FloatField()

    announce_date = models.DateField()
    expire_date = models.DateField()
    record_date = models.DateField()
    payable_date = models.DateField()

    def load_csv(self, line):
        """
        Load csv line split into values and save data
        :param line: str
        :return: Dividend
        """
        values = line.rstrip().split(',')

        self.symbol = values[0]
        self.amount = float(values[1].replace('$', ''))
        self.announce_date = pd.datetime.strptime(values[2], '%m/%d/%y').date()
        self.expire_date = pd.datetime.strptime(values[3], '%m/%d/%y').date()
        self.record_date = pd.datetime.strptime(values[4], '%m/%d/%y').date()
        self.payable_date = pd.datetime.strptime(values[5], '%m/%d/%y').date()

        return self

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.symbol, self.amount, self.announce_date, self.expire_date,
                   self.record_date, self.payable_date]],
            index=[self.expire_date],
            columns=['Symbol', 'Amount', 'Announced Date', 'Expire Date',
                     'Record Date', 'Payable Date']
        )

    def __unicode__(self):
        """
        Output explain this model
        """
        return '{symbol} {expire_date} {amount}'.format(
            symbol=self.symbol,
            expire_date=self.expire_date,
            amount=self.amount
        )


class Earning(models.Model):
    """
    Date est,Date act,Time est,Time act,Symbol,Quarter,EPS est,EPS act,Status
    11/17/09,,During Market,,GRZ,Q3,,,Unconfirmed
    11/17/09,11/17/09,Before Market,5:00:00 AM CST,COV,Q4,0.699,0.11,Verified
    """
    date_est = models.DateField()
    date_act = models.DateField(null=True)
    release = models.CharField(max_length=20)
    time = models.TimeField(null=True)
    symbol = models.CharField(max_length=20)
    quarter = models.CharField(max_length=2)
    esp_est = models.FloatField(null=True)
    esp_act = models.FloatField(null=True)
    status = models.CharField(max_length=20)

    unique_together = (('date_est', 'symbol', 'status'),)

    def load_csv(self, line):
        """
        Load csv line split into values and save data
        :param line: str
        :return: Dividend
        """
        values = line.rstrip().split(',')

        self.date_est = pd.datetime.strptime(values[0], '%m/%d/%y').date()
        self.date_act = pd.datetime.strptime(values[1], '%m/%d/%y').date() if values[1] else None
        self.release = values[2]
        self.time = (pd.datetime.strptime(values[3][:values[3].rindex(' ')], '%I:%M:%S %p').time()
                     if values[3] else None)
        self.symbol = values[4]
        self.quarter = values[5]
        self.esp_est = float(values[6]) if values[6] else None
        self.esp_act = float(values[7]) if values[7] else None
        self.status = values[8]

        return self

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.date_est, self.date_act, self.release, self.time,
                   self.symbol, self.quarter, self.esp_est, self.esp_act, self.status]],
            index=[self.date_est],
            columns=['Date Est', 'Date Act', 'Time Est', 'Time Act',
                     'Symbol', 'Quarter', 'ESP Est', 'ESP Act', 'Status']
        )

    def __unicode__(self):
        """
        Output explain this model
        """
        return '{symbol} {date_est} {esp_act}'.format(
            symbol=self.symbol,
            date_est=self.date_est,
            esp_act=self.esp_act
        )


class TreasuryInstrument(models.Model):
    """
    us.gov.security
    constant.maturity.nominal.1year.annual

    "Series Description","Market yield on U.S. Treasury securities at 1-year   constant maturity, quoted on investment basis"
    "Unit:","Percent:_Per_Year"
    "Multiplier:","1"
    "Currency:","NA"
    "Unique Identifier: ","H15/H15/RIFLGFCY01_N.A"
    "Time Period","RIFLGFCY01_N.A"
    1962,3.10

    annual as 360 days, monthly as 30 days, weekly as 5 days
    """
    name = models.CharField(max_length=200)
    instrument = models.CharField(max_length=200, null=True)
    maturity = models.CharField(max_length=10)

    description = models.TextField()
    unit = models.CharField(max_length=200)
    multiplier = models.FloatField()
    currency = models.CharField(max_length=10)
    unique_identifier = models.CharField(max_length=200, unique=True)
    time_period = models.CharField(max_length=200)

    time_frame = models.CharField(max_length=20)

    def load_csv(self, lines):
        """
        Load csv lines data into values
        :param lines: str
        :return: TreasuryInstrument
        """
        values = [line.rstrip().split('","')[1].replace('"', '') for line in lines]

        self.description = values[0]
        self.unit = values[1]
        self.multiplier = float(values[2])
        self.currency = values[3]
        self.unique_identifier = values[4]
        self.time_period = values[5]

        return self

    def to_hdf(self):
        """
        :return: DataFrame
        """
        return DataFrame(
            data=[[self.name, self.instrument, self.time_frame, self.unit, self.multiplier,
                   self.currency, self.time_period, self.description]],
            index=[self.unique_identifier],
            columns=['Name', 'Instrument', 'Time Frame', 'Unit',
                     'Multiplier', 'Currency', 'Time Period', 'Description']
        )

    def __unicode__(self):
        """
        Output explain this model
        """
        return '{name} {instrument} {maturity} {time_frame}'.format(
            name=self.name, instrument=self.instrument if self.instrument else '',
            maturity=self.maturity, time_frame=self.time_frame,
        )


class TreasuryInterest(models.Model):
    """
    1962-02-20,3.31
    2008,1.83
    2009,0.47
    """
    treasury = models.ForeignKey(TreasuryInstrument, null=True)

    date = models.DateField()
    interest = models.FloatField(null=True)

    def load_csv(self, line):
        """
        Load csv data into values
        :param line: str
        :return: TreasuryInterest
        """
        date_format = {
            'Annual': '%Y',
            'Monthly': '%Y-%m',
            'Weekly': '%Y-%m-%d',
            'Bdays': '%Y-%m-%d',
        }

        values = line.rstrip().split(',')

        self.date = pd.datetime.strptime(values[0], date_format[str(self.treasury.time_frame)]).date()
        self.interest = None if values[1] == 'ND' else float(values[1])

        return self

    def to_hdf(self):
        """
        :return: Series
        """
        return Series([self.interest], index=[self.date])

    def __unicode__(self):
        """
        Output explain this model
        """
        return '{treasury} {date} {interest}'.format(
            treasury=self.treasury, date=self.date, interest=self.interest
        )


















