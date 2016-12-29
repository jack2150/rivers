from django.db import models


class TechnicalRank(models.Model):
    """
    Technical analysis opinion, daily update
    """
    # Weak-Form Hypothesis
    symbol = models.CharField(max_length=6)
    date = models.DateField()
    unique_together = (('symbol', 'date'),)

    # third party ranking provider
    market_edge = models.IntegerField(
        choices=((0, 'Strong Sell'), (1, 'Sell'), (3, 'Hold'), (4, 'Buy'), (5, 'Strong Buy'),
                 (None, 'No score')),
        max_length=20, help_text='Market edge ranking', null=True, default=3
    )
    bar_chart = models.IntegerField(
        choices=((0, 'Strong Sell'), (1, 'Sell'), (3, 'Hold'), (4, 'Buy'), (5, 'Strong Buy'),
                 (None, 'No score')),
        max_length=20, help_text='Market edge ranking', null=True, default=3
    )
    chartmill = models.IntegerField(
        choices=((0, 'Strong Sell'), (1, 'Sell'), (3, 'Hold'), (4, 'Buy'), (5, 'Strong Buy'),
                 (None, 'No score')),
        max_length=20, help_text='Market edge ranking', null=True, default=3
    )


class TechnicalOpinion(models.Model):
    """
    Technical analysis opinion, daily update
    """
    # Weak-Form Hypothesis
    symbol = models.CharField(max_length=6)
    date = models.DateField()

    # unique data
    unique_together = (('symbol', 'date'),)

    # own charting
    # SMA 200.50, RSI 25.10
    sma50_trend = models.CharField(
        max_length=10, choices=(('bullish', 'Bullish'), ('range', 'Range'), ('bearish', 'Bearish')),
        help_text='Simple Moving Average 50, trending'
    )
    sma200_trend = models.CharField(
        max_length=10, choices=(('bullish', 'Bullish'), ('range', 'Range'), ('bearish', 'Bearish')),
        help_text='Simple Moving Average 200, trending'
    )
    sma_cross = models.BooleanField(
        default=False, help_text='SMA 200.50 cross'
    )
    rsi_score = models.CharField(
        choices=(('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')),
        max_length=10, help_text='RSI, x > 70 overbought, x < 30 oversold'
    )

    # volume profile
    volume_profile = models.CharField(
        max_length=10, choices=(('above', 'Above'), ('middle', 'Middle'), ('below', 'Below')),
        help_text='Enter long/short above or below market average'
    )

    # vwap, acc-dist
    vwap_average = models.CharField(
        max_length=10, choices=(('above', 'Above'), ('middle', 'Middle'), ('below', 'Below')),
        help_text='Volume weight average price, 1 month'
    )
    acc_dist = models.CharField(
        max_length=10, choices=(('increase', 'Increase'), ('decrease', 'Decrease')),
        help_text='Public share accumulation distribution'
    )

    # Ichimoku 26.9
    ichimoku_cloud = models.CharField(
        max_length=10, choices=(('above', 'Above'), ('middle', 'Middle'), ('below', 'Below')),
        help_text='Price distance from cloud'
    )
    ichimoku_color = models.CharField(
        max_length=10, choices=(('green', 'Green'), ('red', 'Red')),
        help_text='Ichimoku cloud color'
    )
    ichimoku_base = models.CharField(
        max_length=10, choices=(('above', 'Above'), ('cross', 'Cross'), ('below', 'Below')),
        help_text='Price from base line (26-days, yellow)'
    )
    ichimoku_conversion = models.CharField(
        max_length=10, choices=(('above', 'Above'), ('cross', 'Cross'), ('below', 'Below')),
        help_text='Conversion line (blue) move from base line (yellow)'
    )

    # parabolic 0.2, dmi 14
    parabolic_trend = models.CharField(
        max_length=10, choices=(('bullish', 'Bullish'), ('bearish', 'Bearish')),
        help_text='Parabolic 0.2 dot trending'
    )
    parabolic_cross = models.BooleanField(
        default=False, help_text='Parabolic 0.2 dot crossing'
    )
    dmi_trend = models.CharField(
        max_length=10, choices=(('bullish', 'Bullish'), ('bearish', 'Bearish')),
        help_text='DMI 14, which higher DI+ (blue) bullish, DI- (yellow) bearish'
    )
    dmi_cross = models.BooleanField(
        default=False, help_text='DMI 14 cross, DI+ (blue) cross DI- (yellow)'
    )

    # stochastic, 20.5.3, 20.20.5, 20.20.15
    stoch_score0 = models.CharField(
        max_length=10, choices=(
            ('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')
        ), help_text='Stochastic full 14.3.3, x > 80 overbought, x < 20 oversold'
    )
    stoch_score1 = models.CharField(
        max_length=10, choices=(
            ('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')
        ), help_text='Stochastic full 20.5.5, x > 80 overbought, x < 20 oversold'
    )
    stoch_score2 = models.CharField(
        max_length=10, choices=(
            ('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')
        ), help_text='Stochastic full 20.15.15, x > 80 overbought, x < 20 oversold'
    )

    # band 20.2, macd 26.9
    band_score = models.CharField(
        max_length=10, choices=(
            ('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')
        ), help_text='Bollinger band 20.2, overbought or oversold'
    )
    macd_score = models.CharField(
        max_length=10, choices=(
            ('overbought', 'Overbought'), ('middle', 'Middle'), ('oversold', 'Oversold')
        ), help_text='MACD 26.9, overbought or oversold'
    )

    # research extra
    extra_analysis = models.IntegerField(
        help_text='How many extra technical analysis that you reviews'
    )

    # note
    description = models.TextField(
        help_text='Extra note you want to write down', blank=True, null=True
    )



# todo: optimize technical opinion into less