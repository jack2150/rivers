# option stat, top largest volume strategy, greek chart, etc...
import datetime
from django.db import models

from base.ufunc import UploadRenameImage
from opinion.group.report.models import UnderlyingReport


class OptionStat(models.Model):
    """
    Daily update for option stat
    """
    report = models.OneToOneField(UnderlyingReport, null=True, blank=True)

    provide = models.BooleanField(default=False)
    date = models.DateField(default=datetime.datetime.now)

    iv_move_chart = models.ImageField(
        blank=True, default=None, null=True, help_text='Stock price with hv/iv chart',
        upload_to=UploadRenameImage('option/iv_move')
    )
    stat_image = models.ImageField(
        blank=True, default=None, null=True, help_text='Option statistics image',
        upload_to=UploadRenameImage('option/stat')
    )

    # iv, short vs long term, lowest iv strike
    iv_term = models.BooleanField(
        default=True, help_text='Is IV short spike vs long term stable?'
    )
    iv_skew = models.BooleanField(
        default=True, help_text='ATM strike IV are lowest? or OTM?'
    )
    iv_covered_chart = models.ImageField(
        blank=True, default=None, null=True, help_text='IV & covered chart',
        upload_to=UploadRenameImage('option/iv_covered')
    )

    # theta
    theta_skew = models.BooleanField(
        default=True, help_text='ATM strike theta are lowest?'
    )
    vega_skew = models.BooleanField(
        default=True, help_text='ATM strike vage are lowest?'
    )
    theta_vega_chart = models.ImageField(
        blank=True, default=None, null=True, help_text='theta & vega statistics image',
        upload_to=UploadRenameImage('option/theta_vega')
    )

    # open interest
    vol_oi_chart = models.ImageField(
        blank=True, default=None, null=True, help_text='open interest & volume chart image',
        upload_to=UploadRenameImage('option/vol_oi')
    )

    # timesale raw
    raw_data = models.TextField(default='', blank=True, null=True)

    unique_together = (('report', 'date'),)

    def __unicode__(self):
        return 'OptionStat {symbol} {date}'.format(
            symbol=self.report.symbol, date=self.date
        )


class OptionStatIV(models.Model):
    """
    iv expected price move range
    iv chart move, incoming iv change analysis

    Use for expect possible incoming iv move
    that will affect option pricing high or low
    useful when trading option strategy (butterfly)
    """
    option_stat = models.OneToOneField(OptionStat)

    iv_52w_high = models.FloatField(default=0, blank=True)
    iv_52w_low = models.FloatField(default=0, blank=True)
    iv_current_pct = models.FloatField(default=0, blank=True)
    hv_52w_high = models.FloatField(default=0, blank=True)
    hv_52w_low = models.FloatField(default=0, blank=True)
    hv_current_pct = models.FloatField(default=0, blank=True)
    iv = models.FloatField(default=0, blank=True)
    vwap = models.FloatField(default=0, blank=True)


class OptionStatSizzle(models.Model):
    """
    Use for direction expectation
    sizzle, index vs 5-days average

    sizzle index mean (call/put)
    today options volume vs 5-day volume
    if higher, mean stock have some news and quite active

    iv sizzle
    today iv vs 5-days iv average, maybe jump or maybe drop

    stock sizzle
    stock volume big jump or big drop vs 5-day average

    pc ratio
    people buy more put or more call
    if more put mean more protection (1st), or vertical or naked
    if more call, mean more covered or vertical or naked
    """
    option_stat = models.OneToOneField(OptionStat)

    index = models.FloatField(default=0, blank=True)
    call = models.FloatField(default=0, blank=True)
    put = models.FloatField(default=0, blank=True)
    iv = models.FloatField(default=0, blank=True)
    stock = models.FloatField(default=0, blank=True)
    pc_ratio = models.FloatField(default=0, blank=True)


class OptionStatBidAsk(models.Model):
    """
    Bit/ask use for enter/exit price expectation
    if most people enter bid below,
    then u at above bid mostly will hard to fill

    Delta use for know what most trade probability
    you can simply find out why it traded
    call otm: mostly naked call (straddle)
    call atm: mostly covered call or vertical
    call itm: bid/ask too wide, no trade-able

    put otm: mostly naked put
    put atm: mostly protection or vertical
    put itm: previous protection, bid/ask too wide
    """
    option_stat = models.ForeignKey(OptionStat)

    name = models.CharField(
        choices=(('call', 'Call'), ('put', 'Put'), ('total', 'Total')),
        max_length=20
    )

    volume = models.IntegerField(default=0, help_text='volume')

    bid_below = models.IntegerField(default=0, help_text='%')
    ask_above = models.IntegerField(default=0, help_text='%')
    between_market = models.IntegerField(default=0, help_text='%')

    delta_0_20 = models.IntegerField(default=0, help_text='%')
    delta_20_40 = models.IntegerField(default=0, help_text='%')
    delta_40_60 = models.IntegerField(default=0, help_text='%')
    delta_60_80 = models.IntegerField(default=0, help_text='%')
    delta_80_100 = models.IntegerField(default=0, help_text='%')


class OptionStatOpenInterest(models.Model):
    """
    Top 3 open interest (call & put) totally 6, explain
    """
    option_stat = models.ForeignKey(OptionStat)

    ex_date = models.DateField()
    strike = models.FloatField(default=0)
    open_interest = models.BigIntegerField(default=0)

    name = models.CharField(
        choices=(('call', 'Call'), ('put', 'Put')), max_length=20
    )
    side = models.CharField(
        choices=(('long', 'Long'), ('short', 'Short'), ('mix', 'Mix')), max_length=20
    )
    volume = models.CharField(
        choices=(('add', 'Add'), ('reduce', 'Reduce'), ('hold', 'Hold')), max_length=20
    )

    direction = models.CharField(
        choices=(('bull', 'Bull'), ('neutral', 'Neutral'), ('bear', 'Bear')), max_length=20
    )


class OptionStatTimeSaleTrade(models.Model):
    """
    Single timesale order
    """
    option_stat = models.ForeignKey(OptionStat)

    time = models.TimeField()

    option = models.CharField(max_length=100, blank=True, null=True)
    ex_date = models.DateField()
    strike = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    name = models.CharField(max_length=20, blank=True, null=True)
    qty = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mark = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    trade = models.CharField(max_length=20, blank=True, null=True, default='BUY/SELL')
    exchange = models.CharField(max_length=50, blank=True, null=True, default='BEST')

    bid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ask = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    delta = models.FloatField(default=0)
    iv = models.FloatField(default=0)
    underlying_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    condition = models.CharField(max_length=50, blank=True, null=True, default='')

    # extra self add
    fill = models.CharField(
        choices=(('enter', 'ENTER'), ('exit', 'EXIT')),
        max_length=50, blank=True, null=True, default='',
        help_text='Using yesterday thinkback'
    )

    def __unicode__(self):
        trade = {
            'BUY': '+', 'SELL': '-', 'BUY/SELL': '+-'
        }

        return '%s %s%d %s 100 %s @%.2f LMT' % (
            self.trade.upper(),
            trade[str(self.trade)],
            self.qty,
            self.option_stat.report.symbol.upper(),
            self.option,
            float(self.price)
        )


class OptionStatTimeSaleContract(models.Model):
    """
    Summary timesale data by contract
    """
    option_stat = models.ForeignKey(OptionStat)

    option = models.CharField(max_length=100, blank=True, null=True)
    ex_date = models.DateField()
    strike = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    name = models.CharField(max_length=20, blank=True, null=True)
    qty = models.IntegerField(default=0)

    bid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ask = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mark = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __unicode__(self):
        return '%d %s 100 %s @%.2f LMT' % (
            self.qty,
            self.option_stat.report.symbol.upper(),
            self.option,
            float(self.price)
        )
