from django.db import models
import pandas as pd
from pandas.util.testing import DataFrame


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



























