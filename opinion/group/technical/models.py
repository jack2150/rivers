import datetime
from django.db import models

from opinion.group.report.models import ReportEnter


class TechnicalRank(models.Model):
    """
    Technical analysis opinion, daily update
    """
    # Weak-Form Hypothesis - third party ranking provider
    report = models.OneToOneField(ReportEnter, null=True, blank=True)

    def __unicode__(self):
        if self.report:
            report = '%s %s' % (self.report.symbol, self.report.date)
        else:
            report = 'New'
        return 'TechnicalRank {report}'.format(report=report)


class TechnicalMarketedge(models.Model):
    tech_rank = models.OneToOneField(TechnicalRank)

    # market edge
    opinion = models.IntegerField(
        choices=(
            (0, 'None'),
            (1, '1 Long'), (2, '2 Neutral from Long'),
            (3, '3 Neutral'),
            (4, '4 Neutral from Avoid'), (5, '5 Avoid')
        ),
        help_text='Second opinion', default=3
    )
    score = models.IntegerField(default=0)
    date = models.DateField(null=True, blank=True, help_text='Opinion date')
    fprice = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0, help_text='Formed price'
    )
    crate = models.FloatField(
        default=0, help_text='% move left, +20 long > +8 neutral -4 < short -10'
    )
    power = models.IntegerField(
        default=0, help_text='Power rating, mix of 7 indicators, long > 60 neutral <-27 short'
    )
    recommend = models.TextField(
        blank=True, null=True, default='', help_text='Recommendation'
    )
    resist = models.DecimalField(
        default=0, max_digits=10, decimal_places=2, help_text='Resistance price'
    )
    support = models.DecimalField(
        default=0, max_digits=10, decimal_places=2, help_text='Support price'
    )
    stop = models.DecimalField(
        default=0, max_digits=10, decimal_places=2, help_text='Sell stop price'
    )
    position = models.IntegerField(
        default=0, help_text='Previous 20-days stop-loss condition'
    )

    def __unicode__(self):
        return 'MarketEdge {opinion} ({crate})'.format(
            opinion=self.opinion, crate=self.crate
        )


class TechnicalBarchart(models.Model):
    tech_rank = models.OneToOneField(TechnicalRank)

    # bar chart
    overall = models.IntegerField(
        default=0, help_text='Overall average signal calculated from all 13 indicators'
    )
    strength = models.IntegerField(
        default=0, help_text='Long-term measurement of the historical strength'
    )
    direction = models.IntegerField(
        default=0, help_text='Short-term (3-Day) measurement of the movement'
    )
    pre_day = models.IntegerField(default=0, help_text='Yesterday overall signal')
    pre_week = models.IntegerField(default=0, help_text='Last week overall signal')
    pre_month = models.IntegerField(default=0, help_text='Last month overall signal')

    day20 = models.IntegerField(default=0, help_text='Short Term average 20 days')
    day50 = models.IntegerField(default=0, help_text='Medium Term average 50 days')
    day100 = models.IntegerField(default=0, help_text='Long Term 100 days')

    resist = models.DecimalField(
        default=0, max_digits=10, decimal_places=2, help_text='Resistance price'
    )
    support = models.DecimalField(
        default=0, max_digits=10, decimal_places=2, help_text='Support price'
    )

    def __unicode__(self):
        return 'Barchart {overall} ({direction})'.format(
            overall=self.overall, direction=self.direction
        )


class TechnicalChartmill(models.Model):
    tech_rank = models.OneToOneField(TechnicalRank)

    # chartmill
    rank = models.IntegerField(help_text='Technical rating', default=5)
    setup = models.IntegerField(help_text='Setup analysis', default=5)
    p2sr = models.CharField(
        choices=(('high', 'High'), ('middle', 'Middle'), ('low', 'Low')),
        help_text='Support/resistance analysis', default='middle', max_length=20
    )
    good = models.IntegerField(help_text='Good point', default=0)
    bad = models.IntegerField(help_text='Bad point', default=0)

    trade_signal = models.CharField(
        choices=(('long', 'Long'), ('short', 'Short')), default='long',
        max_length=20, help_text='Possible trading setup signal'
    )
    trade_entry = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    trade_exit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    trade_capital = models.FloatField(default=0, help_text='Capital allocate to this trade')

    def __unicode__(self):
        return 'Chartmill {rank} ({setup})'.format(
            rank=self.rank, setup=self.setup
        )


class TechnicalOpinion(models.Model):
    """
    Technical analysis opinion, daily update
    """
    # Weak-Form Hypothesis
    report = models.OneToOneField(ReportEnter, null=True, blank=True)
    timeframe = models.CharField(
        choices=(('minute', 'Minute'), ('hour', 'Hour'), ('Day', 'Day'),
                 ('week', 'Week'), ('month', 'Month')),
        max_length=20, help_text='Timeframe for this analysis', default='Day'
    )
    unique_together = (('report', 'timeframe'),)

    def __unicode__(self):
        if self.report.id:
            report = '%s %s' % (self.report.symbol, self.report.date)
        else:
            report = 'New'
        return 'TechnicalOpinion {report}'.format(report=report)


class TechnicalTick(models.Model):
    tick_next = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')),
        max_length=20, help_text='Today move, predict next move, tick color', default='range'
    )
    tick_pattern = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')),
        max_length=20, help_text='Auto pattern predict move', default='range'
    )
    tick_fprice = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')),
        max_length=20, help_text='Fibonacci price extension in latest trend', default='range'
    )
    tick_ftime = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')),
        max_length=20, help_text='Fibonacci time extension in latest trend', default='range'
    )
    tick_fans = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')),
        max_length=20, help_text='Fibonacci fans in latest trend', default='range'
    )
    tick_pfork = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')),
        max_length=20, help_text='Andrew pitch fork in latest trend', default='range'
    )
    tick_cycle = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')),
        max_length=20, help_text='Cycle chart next trend', default='range'
    )

    tech_op = models.OneToOneField(TechnicalOpinion, null=True, blank=True, default=None)
    tech_desc = models.TextField(blank=True, default='', help_text='5 mins, analysis & projection')

    # chance
    bull_chance = models.IntegerField(default=16, help_text='Price move bullish')
    range_chance = models.IntegerField(default=68, help_text='Price in volatility range')
    bear_chance = models.IntegerField(default=16, help_text='Price move bearish')


class TechnicalSma(models.Model):
    # parameters
    sma_period0 = models.IntegerField(default=50, help_text='Short period')
    sma_period1 = models.IntegerField(default=200, help_text='Long period')

    # SMA 200.50, RSI 25.10
    sma50x200_trend = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')),
        max_length=20, help_text='Sma 50x200 primary direction', default='range'
    )
    sma50x200_gap = models.CharField(
        choices=(('small', 'Small'), ('range', 'range'), ('big', 'Big'), ('cross', 'Cross')),
        max_length=20, help_text='Sma gap between 50x200', default='range'
    )
    rsi_score = models.CharField(
        choices=(('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')),
        max_length=20, help_text='RSI, x > 70 overbought, x < 30 oversold', default='middle'
    )

    tech_op = models.OneToOneField(TechnicalOpinion, null=True, blank=True, default=None)
    tech_desc = models.TextField(blank=True, default='', help_text='5 mins, analysis & projection')

    # chance
    bull_chance = models.IntegerField(default=16, help_text='Price move bullish')
    range_chance = models.IntegerField(default=68, help_text='Price in volatility range')
    bear_chance = models.IntegerField(default=16, help_text='Price move bearish')


class TechnicalVolume(models.Model):
    # volume profile, vwap, acc-dist good
    volume_profile = models.CharField(
        choices=(('above', 'Above'), ('middle', 'Middle'), ('below', 'Below')),
        max_length=20, help_text='Volume profile', default='middle'
    )
    vwap_average = models.CharField(
        choices=(('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')),
        max_length=20, help_text='VWAP monthly', default='middle'
    )
    acc_dist = models.CharField(
        choices=(('add', 'Add'), ('reduce', 'Reduce')),
        max_length=20, help_text='Share acc/dist', default='add'
    )

    tech_op = models.OneToOneField(TechnicalOpinion, null=True, blank=True, default=None)
    tech_desc = models.TextField(blank=True, default='', help_text='5 mins, analysis & projection')

    # chance
    bull_chance = models.IntegerField(default=16, help_text='Price move bullish')
    range_chance = models.IntegerField(default=68, help_text='Price in volatility range')
    bear_chance = models.IntegerField(default=16, help_text='Price move bearish')


class TechnicalIchimoku(models.Model):
    ichimoku_cloud = models.CharField(
        choices=(('above', 'Above'), ('middle', 'Middle'), ('below', 'Below')),
        max_length=20, help_text='Price distance from cloud', default='middle'
    )
    ichimoku_color = models.CharField(
        choices=(('green', 'Green'), ('red', 'Red')),
        max_length=20, help_text='Ichimoku cloud color', default='green'
    )
    ichimoku_base = models.CharField(
        choices=(('above', 'Above'), ('cross', 'Cross'), ('below', 'Below')),
        max_length=20, help_text='Price from base line (26-days, yellow)', default='above'
    )
    ichimoku_convert = models.CharField(
        choices=(('above', 'Above'), ('cross', 'Cross'), ('below', 'Below')),
        max_length=20, help_text='Cross blue line (short term)yellow (long term)', default='above'
    )

    tech_op = models.OneToOneField(TechnicalOpinion, null=True, blank=True, default=None)
    tech_desc = models.TextField(blank=True, default='', help_text='5 mins, analysis & projection')

    # chance
    bull_chance = models.IntegerField(default=16, help_text='Price move bullish')
    range_chance = models.IntegerField(default=68, help_text='Price in volatility range')
    bear_chance = models.IntegerField(default=16, help_text='Price move bearish')


class TechnicalParabolic(models.Model):
    parabolic_trend = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')),
        max_length=20, help_text='Parabolic 0.2 dot trending', default='bull'
    )
    parabolic_cross = models.BooleanField(
        default=False, help_text='Parabolic 0.2 dot crossing'
    )
    dmi_trend = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')), default='bull',
        max_length=20, help_text='DMI 14 lead? DI+ (blue) bull, DI- (yellow) bear'
    )
    dmi_cross = models.BooleanField(
        default=False, help_text='DMI 14 cross? DI+ (blue) cross DI- (yellow)'
    )

    tech_op = models.OneToOneField(TechnicalOpinion, null=True, blank=True, default=None)
    tech_desc = models.TextField(blank=True, default='', help_text='5 mins, analysis & projection')

    # chance
    bull_chance = models.IntegerField(default=16, help_text='Price move bullish')
    range_chance = models.IntegerField(default=68, help_text='Price in volatility range')
    bear_chance = models.IntegerField(default=16, help_text='Price move bearish')


class TechnicalStoch(models.Model):
    # stochastic, good
    darvas_box = models.CharField(
        choices=(('upper', 'Upper'), ('middle', 'Middle'), ('lower', 'Lower')),
        max_length=20, help_text='Price in darvas box', default='middle'
    )
    darvas_signal = models.CharField(
        choices=(('long', 'Long'), ('short', 'Short')), default='long',
        max_length=20, help_text='Darvas box latest trade signal'
    )
    condensed_candle = models.IntegerField(
        choices=((1, 'Signal 1'), (2, 'Signal 2'), (3, 'Signal 3')), default=2,
        help_text='Condensed candle latest signal'
    )
    condensed_chance = models.IntegerField(default=50, help_text='Condensed candle signal chance')

    stoch_full = models.CharField(
        choices=(('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')),
        max_length=20, help_text='Stochastic full', default='middle'
    )

    tech_op = models.OneToOneField(TechnicalOpinion, null=True, blank=True, default=None)
    tech_desc = models.TextField(blank=True, default='', help_text='5 mins, analysis & projection')

    # chance
    bull_chance = models.IntegerField(default=16, help_text='Price move bullish')
    range_chance = models.IntegerField(default=68, help_text='Price in volatility range')
    bear_chance = models.IntegerField(default=16, help_text='Price move bearish')


class TechnicalBand(models.Model):
    # band 20.2, macd 26.9, good
    band_score = models.CharField(
        choices=(('upper', 'Upper'), ('middle', 'Middle'), ('lower', 'Lower')),
        max_length=20, help_text='Bband, support resistance', default='middle'
    )
    macd_score = models.IntegerField(
        choices=((1, 'Bull++'), (2, 'Bull'), (3, 'Hold'), (4, 'Bear'), (5, 'Bear++')),
        help_text='MACD 26.9, trend', default=3
    )

    tech_op = models.OneToOneField(TechnicalOpinion, null=True, blank=True, default=None)
    tech_desc = models.TextField(blank=True, default='', help_text='5 mins, analysis & projection')

    # chance
    bull_chance = models.IntegerField(default=16, help_text='Price move bullish')
    range_chance = models.IntegerField(default=68, help_text='Price in volatility range')
    bear_chance = models.IntegerField(default=16, help_text='Price move bearish')


class TechnicalFw(models.Model):
    # FW MOBO & MMG, good
    fw_mobo_trend = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')), default='bull',
        max_length=20, help_text='FW Momentum Breakout Bands, major trend'
    )
    fw_mobo_signal = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')), default='bull',
        max_length=20, help_text='FW Momentum Breakout Bands color'
    )
    fw_mmg_signal = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')), default='bull',
        max_length=20, help_text='Volume & price momentum latest signal'
    )
    fw_mmg_trend = models.CharField(
        choices=(('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')),
        max_length=20, help_text='Volume & price momentum trend', default='middle'
    )

    tech_op = models.OneToOneField(TechnicalOpinion, null=True, blank=True, default=None)
    tech_desc = models.TextField(blank=True, default='', help_text='5 mins, analysis & projection')

    # chance
    bull_chance = models.IntegerField(default=16, help_text='Price move bullish')
    range_chance = models.IntegerField(default=68, help_text='Price in volatility range')
    bear_chance = models.IntegerField(default=16, help_text='Price move bearish')


class TechnicalTTM(models.Model):
    # ttm, good
    ttm_trend = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')), default='bull',
        max_length=20, help_text='TTM trend bar color'
    )
    ttm_alert = models.CharField(
        choices=(('none', 'None'), ('buy', 'Buy'), ('sell', 'Sell')), default='none',
        max_length=20, help_text='TTM scalper alert signal'
    )
    ttm_linear = models.CharField(
        choices=(('above', 'Above'), ('middle', 'Middle'), ('below', 'Below')), default='middle',
        max_length=20, help_text='TTM Linear Regression Channel'
    )
    ttm_squeeze = models.CharField(
        choices=(('bull', 'On & green'), ('bear', 'On & red'), ('none', 'Indicator off')),
        help_text='TTM Squeeze, trade dot green=on red=off, bar green=bull red=bear',
        default='off', max_length=20,
    )
    ttm_wave = models.IntegerField(
        choices=((1, 'Bear & big gap'), (2, 'Bear & small gap'),
                 (3, 'No & big gap'), (3, 'No & small gap'),
                 (4, 'Green & small gap'), (5, 'Green & big gap')),
        help_text='TTM Wave, trend wave & high low', default=3
    )

    tech_op = models.OneToOneField(TechnicalOpinion, null=True, blank=True, default=None)
    tech_desc = models.TextField(blank=True, default='', help_text='5 mins, analysis & projection')

    # chance
    bull_chance = models.IntegerField(default=16, help_text='Price move bullish')
    range_chance = models.IntegerField(default=68, help_text='Price in volatility range')
    bear_chance = models.IntegerField(default=16, help_text='Price move bearish')


class TechnicalPivot(models.Model):
    # pivot & trend noise, good
    pivot_point = models.CharField(
        choices=(('support', 'Support'), ('middle', 'Middle'), ('resistance', 'Resistance')),
        max_length=20, help_text='Pivot point weekly', default='middle'
    )
    four_percent = models.CharField(
        choices=(('bull', 'Bull'), ('bear', 'Bear')), default='bull',
        max_length=20, help_text='4 percent mode',
    )
    trend_noise = models.CharField(
        choices=(('noise', 'Noise'), ('middle', 'Middle'), ('trend', 'Trend')), default='trend',
        max_length=20, help_text='TrendNoiseBalance, trend > 50, noise < 50'
    )

    tech_op = models.OneToOneField(TechnicalOpinion, null=True, blank=True, default=None)
    tech_desc = models.TextField(blank=True, default='', help_text='5 mins, analysis & projection')

    # chance
    bull_chance = models.IntegerField(default=16, help_text='Price move bullish')
    range_chance = models.IntegerField(default=68, help_text='Price in volatility range')
    bear_chance = models.IntegerField(default=16, help_text='Price move bearish')


class TechnicalFreeMove(models.Model):
    # point of control, good
    tpo_profile = models.CharField(
        choices=(('above', 'Above'), ('within', 'Within'), ('below', 'Below')),
        max_length=20, help_text='Point Of Control, 70% trade activity', default='middle'
    )
    free_move = models.BooleanField(
        default='normal', help_text='Price about the break S/R?'
    )
    relative_vol = models.BooleanField(
        default='normal', help_text='Support/resistance break?'
    )
    market_forecast = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')), default='range',
        max_length=20, help_text='Momentum, NearTerm, and Intermediate'
    )

    tech_op = models.OneToOneField(TechnicalOpinion, null=True, blank=True, default=None)
    tech_desc = models.TextField(blank=True, default='', help_text='5 mins, analysis & projection')

    # chance
    bull_chance = models.IntegerField(default=16, help_text='Price move bullish')
    range_chance = models.IntegerField(default=68, help_text='Price in volatility range')
    bear_chance = models.IntegerField(default=16, help_text='Price move bearish')


class TechnicalZigZag(models.Model):
    # zig zag, good
    zigzag_pct = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')), default='range',
        max_length=20, help_text='ZigZagPercent price general trend'
    )
    zigzag_sign = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')), default='range',
        max_length=20, help_text='ZigZagSign minor market move'
    )

    # aroon, good
    aroon_ind = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')), default='range',
        max_length=20, help_text='Aroon Indicator'
    )
    aroon_osc = models.CharField(
        choices=(('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')),
        max_length=20, help_text='Aroon Oscillator', default='middle'
    )

    tech_op = models.OneToOneField(TechnicalOpinion, null=True, blank=True, default=None)
    tech_desc = models.TextField(blank=True, default='', help_text='5 mins, analysis & projection')

    # chance
    bull_chance = models.IntegerField(default=16, help_text='Price move bullish')
    range_chance = models.IntegerField(default=68, help_text='Price in volatility range')
    bear_chance = models.IntegerField(default=16, help_text='Price move bearish')


# todo: report class
