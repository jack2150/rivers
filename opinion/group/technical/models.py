import datetime
from django.db import models


class TechnicalRank(models.Model):
    """
    Technical analysis opinion, daily update
    """
    # Weak-Form Hypothesis
    symbol = models.CharField(max_length=6)
    date = models.DateField(default=datetime.datetime.now)
    unique_together = (('symbol', 'date'),)

    # third party ranking provider
    market_edge = models.IntegerField(
        choices=((0, 'Strong Sell'), (1, 'Sell'), (3, 'Hold'), (4, 'Buy'), (5, 'Strong Buy'),
                 (-1, 'No score')),
        help_text='Market edge ranking', default=-1
    )
    bar_chart = models.IntegerField(
        choices=((0, 'Strong Sell'), (1, 'Sell'), (3, 'Hold'), (4, 'Buy'), (5, 'Strong Buy'),
                 (-1, 'No score')),
        help_text='Market edge ranking', default=-1
    )
    chartmill = models.IntegerField(
        choices=((0, 'Strong Sell'), (1, 'Sell'), (3, 'Hold'), (4, 'Buy'), (5, 'Strong Buy'),
                 (-1, 'No score')),
        help_text='Market edge ranking', default=-1
    )

    description = models.TextField(blank=True, null=True, help_text='Technical rank detail')

    def __unicode__(self):
        return 'TechnicalRank {symbol} {date}'.format(symbol=self.symbol, date=self.date)


class TechnicalOpinion(models.Model):
    """
    Technical analysis opinion, daily update
    """
    # Weak-Form Hypothesis
    symbol = models.CharField(max_length=6)
    date = models.DateField(default=datetime.datetime.now)
    timeframe = models.CharField(
        choices=(('minute', 'Minute'), ('hour', 'Hour'), ('Day', 'Day'),
                 ('week', 'Week'), ('month', 'Month')),
        max_length=10, help_text='Timeframe for this analysis', default='Day'
    )
    unique_together = (('symbol', 'date', 'timeframe'),)

    # own charting
    # SMA 200.50, RSI 25.10
    sma50_trend = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')),
        max_length=10, help_text='Simple Moving Average 50, trending', default='range'
    )
    sma200_trend = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')),
        max_length=10, help_text='Simple Moving Average 200, trending', default='range'
    )
    sma_cross = models.BooleanField(
        default=False, help_text='SMA 200.50 cross'
    )
    rsi_score = models.CharField(
        choices=(('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')),
        max_length=10, help_text='RSI, x > 70 overbought, x < 30 oversold', default='middle'
    )

    # volume profile, vwap, acc-dist good
    volume_profile = models.CharField(
        choices=(('above', 'Above'), ('middle', 'Middle'), ('below', 'Below')),
        max_length=10, help_text='Price above or below market average', default='middle'
    )
    vwap_average = models.CharField(
        choices=(('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')),
        max_length=10, help_text='Volume weight average price, 1 month', default='middle'
    )
    acc_dist = models.CharField(
        choices=(('add', 'Add'), ('reduce', 'Reduce')),
        max_length=10, help_text='Public share accumulation distribution', default='add'
    )

    # Ichimoku 26.9, good
    ichimoku_cloud = models.CharField(
        choices=(('above', 'Above'), ('middle', 'Middle'), ('below', 'Below')),
        max_length=10, help_text='Price distance from cloud', default='middle'
    )
    ichimoku_color = models.CharField(
        choices=(('green', 'Green'), ('red', 'Red')),
        max_length=10, help_text='Ichimoku cloud color', default='green'
    )
    ichimoku_base = models.CharField(
        choices=(('above', 'Above'), ('cross', 'Cross'), ('below', 'Below')),
        max_length=10, help_text='Price from base line (26-days, yellow)', default='above'
    )
    ichimoku_convert = models.CharField(
        choices=(('above', 'Above'), ('cross', 'Cross'), ('below', 'Below')),
        max_length=10, help_text='Conversion blue line move from yellow line', default='above'
    )

    # parabolic 0.2, dmi 14, good
    parabolic_trend = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')),
        max_length=10, help_text='Parabolic 0.2 dot trending', default='bull'
    )
    parabolic_cross = models.BooleanField(
        default=False, help_text='Parabolic 0.2 dot crossing'
    )
    dmi_trend = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')), default='bull',
        max_length=10, help_text='DMI 14 lead? DI+ (blue) bull, DI- (yellow) bear'
    )
    dmi_cross = models.BooleanField(
        default=False, help_text='DMI 14 cross? DI+ (blue) cross DI- (yellow)'
    )

    # stochastic, good
    stoch_fast = models.CharField(
        choices=(('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')),
        max_length=10, help_text='Stochastic fast', default='middle'
    )
    stoch_full = models.CharField(
        choices=(('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')),
        max_length=10, help_text='Stochastic full', default='middle'
    )

    # band 20.2, macd 26.9, good
    band_score = models.CharField(
        choices=(('below', 'Below'), ('middle', 'Middle'), ('above', 'Above')),
        max_length=10, help_text='Bband, support resistance', default='middle'
    )
    macd_score = models.IntegerField(
        choices=((1, 'Strong bear'), (2, 'Bear'), (3, 'Hold'), (4, 'Bull'), (5, 'Strong bull')),
        help_text='MACD 26.9, trend', default='middle'
    )

    # FW MOBO & MMG, good
    fw_mobo_trend = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')), default='bull',
        max_length=10, help_text='FW Momentum Breakout Bands, major trend'
    )
    fw_mobo_signal = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')), default='bull',
        max_length=10, help_text='FW Momentum Breakout Bands color'
    )
    fw_mmg_signal = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')), default='bull',
        max_length=10, help_text='Volume & price momentum latest signal'
    )
    fw_mmg_trend = models.CharField(
        choices=(('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')),
        max_length=10, help_text='Volume & price momentum trend', default='middle'
    )

    # pivot & trend noise, good
    pivot_point = models.CharField(
        choices=(('support', 'Support'), ('middle', 'Middle'), ('resistance', 'Resistance ')),
        max_length=10, help_text='Pivot point weekly', default='middle'
    )
    four_percent = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')), default='bull',
        max_length=10, help_text='4 percent mode',
    )
    trend_noise = models.CharField(
        choices=(('noise', 'Noise'), ('middle', 'Middle'), ('trend', 'Trend')), default='trend',
        max_length=10, help_text='TrendNoiseBalance, trend > 50, noise < 50'
    )

    # point of control, good
    tpo_profile = models.CharField(
        choices=(('above', 'Above'), ('within', 'Within'), ('below', 'Below')),
        max_length=10, help_text='Point Of Control, 70% trade activity', default='middle'
    )
    free_move = models.BooleanField(
        default='normal', help_text='Price about the break S/R?'
    )
    relative_vol = models.BooleanField(
        default='normal', help_text='Support/resistance break?'
    )
    market_forecast = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')), default='range',
        max_length=10, help_text='Momentum, NearTerm, and Intermediate'
    )

    # ttm, good
    ttm_trend = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')), default='bull',
        max_length=10, help_text='TTM trend bar color'
    )
    ttm_alert = models.CharField(
        choices=(('none', 'None'), ('buy', 'Buy'), ('sell', 'Sell')), default='none',
        max_length=10, help_text='TTM scalper alert signal'
    )
    ttm_linear = models.CharField(
        choices=(('above', 'Above'), ('middle', 'Middle'), ('below', 'Below')), default='middle',
        max_length=10, help_text='TTM Linear Regression Channel'
    )
    ttm_squeeze = models.CharField(
        choices=(('bull', 'On & green'), ('bear', 'On & red'), ('none', 'Indicator off')),
        help_text='TTM Squeeze, trade dot green=on red=off, bar green=bull red=bear',
        default='off', max_length=10,
    )
    ttm_wave = models.IntegerField(
        choices=((1, 'Bear & big gap'), (2, 'Bear & small gap'),
                 (3, 'No & big gap'), (3, 'No & small gap'),
                 (4, 'Green & small gap'), (5, 'Green & big gap')),
        help_text='TTM Wave, trend wave & high low', default=3
    )

    # zig zag, good
    zigzag_pct = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')), default='range',
        max_length=10, help_text='ZigZagPercent price general trend'
    )
    zigzag_sign = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')), default='range',
        max_length=10, help_text='ZigZagSign minor market move'
    )

    # aroon, good
    aroon_ind = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')), default='range',
        max_length=10, help_text='Aroon Indicator'
    )
    aroon_osc = models.CharField(
        choices=(('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')),
        max_length=10, help_text='Aroon Oscillator', default='middle'
    )

    # research extra & note
    description = models.TextField(help_text='Detail technical note', blank=True, null=True)

    def __unicode__(self):
        return 'TechnicalOpinion {symbol} {date} {timeframe}'.format(
            symbol=self.symbol, date=self.date, timeframe=self.timeframe
        )
