from django.db import models


class MarketMovement(models.Model):
    """
    market move, economics calendar, special market news, update daily
    """
    date = models.DateField(
        help_text='Daily market movement for /ES /NQ /YM /TF /VX', unique=True
    )

    # whole market
    volatility = models.CharField(
        max_length=20,
        choices=(('low', 'Low'), ('normal', 'Normal'), ('high', 'High')),
        help_text='Market volatility /VX or VIX'
    )
    bond = models.CharField(
        max_length=20,
        choices=(('bearish', 'Bearish'), ('neutral', 'Neutral'), ('bullish', 'Bullish')),
        help_text='Bond market /TF'
    )
    commodity = models.CharField(
        max_length=20,
        choices=(('bearish', 'Bearish'), ('neutral', 'Neutral'), ('bullish', 'Bullish')),
        help_text='Commodity /CL /NG /GC /SI'
    )

    currency = models.CharField(
        max_length=20,
        choices=(('bearish', 'Bearish'), ('neutral', 'Neutral'), ('bullish', 'Bullish')),
        help_text='Forex /6J /DX /6E'
    )

    # technical trend, spy only
    previous_short_trend = models.CharField(
        max_length=20,
        choices=(('bearish', 'Bearish'), ('neutral', 'Neutral'), ('bullish', 'Bullish')),
        help_text='Previous short term trend'
    )
    current_short_trend = models.CharField(
        max_length=20,
        choices=(('bearish', 'Bearish'), ('neutral', 'Neutral'), ('bullish', 'Bullish')),
        help_text='Current short term trend'
    )
    previous_long_trend = models.CharField(
        max_length=20,
        choices=(('bearish', 'Bearish'), ('neutral', 'Neutral'), ('bullish', 'Bullish')),
        help_text='Previous long term trend'
    )
    current_long_trend = models.CharField(
        max_length=20,
        choices=(('bearish', 'Bearish'), ('neutral', 'Neutral'), ('bullish', 'Bullish')),
        help_text='Current long term trend'
    )

    # economics calendar
    market_indicator = models.IntegerField(default=0)
    extra_attention = models.IntegerField(default=0)
    key_indicator = models.IntegerField(default=0)
    special_news = models.BooleanField(default=False)
    commentary = models.TextField(
        null=True, blank=True, help_text='Input daily market condition'
    )

    def __unicode__(self):
        return 'MarketMovement {date}'.format(
            date=self.date
        )


class MarketValuation(models.Model):
    """
    macro valuation, Weekly update
    """
    date = models.DateField()

    cli_trend = models.CharField(
        max_length=10,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='Composite leading indicator'
    )

    bci_trend = models.CharField(
        max_length=10,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='Business Cycle Indicator'
    )

    # positive: interest increase, inflation increase, stock increase, sale grow
    # range: interest increase, inflation increase, stock decline, cash grow
    # negative: interest increase, inflation increase, stock decline, cash decline
    market_scenario = models.CharField(
        max_length=20,
        choices=(('very_negative', 'Very Negative'), ('midly_negative', 'Midly Negative'),
                 ('positive', 'Positive')),
        help_text='Inflation, Interest Rates, and Stock Prices'
    )

    # Growth money supply for better economic
    money_supply = models.CharField(
        max_length=10,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='M2 Money supply'
    )

    monetary_policy = models.TextField(
        null=True, blank=True,
        help_text='Monetary policy simple explanation'
    )


class MarketIndicator(models.Model):
    """
    Popular market indicator, weekly update
    """
    date = models.DateField()

    # section: Contrary-Opinion Rules
    # negative: borrow cash to invest, positive: sell share for cash
    fund_cash_ratio = models.CharField(
        max_length=20,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='Mutual fund cash ratio'
    )

    # greek: move up, fear: move down
    fear_greek_index = models.CharField(
        max_length=20,
        choices=(('fear', 'Fear'), ('range', 'Range'), ('greed', 'Greed')),
        help_text='Fear & Greed index'
    )

    # credit balance lower: investor buy, higher: investor sell
    credit_balance = models.CharField(
        max_length=20,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='Market credit balance'
    )

    # market put call buy ratio, higher: more call, bull, lower: more put, bear
    put_call_ratio = models.CharField(
        max_length=20,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='Market put call ratio'
    )

    # lower: investor sell, higher: investor buy
    investor_sentiment = models.CharField(
        max_length=20,
        choices=(('bearish', 'Bearish'), ('neutral', 'Neutral'), ('bullish', 'Bullish')),
        help_text='Investor sentiment'
    )

    # s&p 500 share change,
    futures_trader = models.CharField(
        max_length=20,
        choices=(('bearish', 'Bearish'), ('neutral', 'Neutral'), ('bullish', 'Bullish')),
        help_text='CFTC S&P 500 trader'
    )

    # section: smart money
    # bond conf index, higher: invest in bond, lower: invest in stock
    confidence_index = models.CharField(
        max_length=20,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='Confidence Index'
    )

    # t-bill eurodollar spread,
    # higher: money into t-bill, stock down,
    # lower: money out t-bill, stock up
    ted_spread = models.CharField(
        max_length=20,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='Ted spread'
    )

    # investor borrow more: higher, stock up; borrow less: lower, stock down
    margin_debt = models.CharField(
        max_length=20,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='Margin debt'
    )

    # section: market momentum
    # Breadth of Market: high, more advance price, stock up; low, more decline price, stock down
    market_breadth = models.CharField(
        max_length=20,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='Breadth of Market'
    )

    # below 20: oversold, above: 80 overbought
    ma200day_pct = models.CharField(
        max_length=20,
        choices=(('overbought', 'Overbought'), ('fair_value', 'Fair value'), ('oversold', 'Oversold')),
        help_text='% of S&P 500 Stocks Above 200-Day Moving Average'
    )

    # $trin, Short-Term Trading Index: overbought: sell, oversold: buy
    arms_index = models.CharField(
        max_length=20,
        choices=(('overbought', 'Overbought'), ('fair_value', 'Fair value'), ('oversold', 'Oversold')),
        help_text='Short-Term Trading Arms Index'
    )

    # support and resistant
    support_price = models.FloatField(default=0, help_text='S&P 500 Support')
    resistant_price = models.FloatField(default=0, help_text='S&P 500 Resistant')

    # section: price and volume
    # down theory for market
    dow_phase = models.CharField(
        max_length=20,
        choices=(('accumulate', 'Accumulate'), ('trend', 'Trend'), ('distribute', 'Distribute')),
        help_text='Dow theory phase'
    )
    dow_movement = models.CharField(
        max_length=20,
        choices=(('bullish', 'Bullish'), ('bearish', 'Bearish'),
                 ('medium_swing', 'Medium swing'), ('short_swing', 'Short swing')),
        help_text='Dow theory movement'
    )
    dow_ma200x50 = models.BooleanField(default=False, help_text='MA 50x200 confirm')
    dow_volume = models.BooleanField(default=False, help_text='Trend volume confirm')

    # moving average 50 days with volume confirm
    ma50_confirm = models.BooleanField(default=False, help_text='MA 50 & large volume')

    # market fair value, undervalue: buy, overvalue: sell
    fair_value_trend = models.CharField(
        max_length=20,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='Market fair value'
    )


class EconomicReview(models.Model):
    """
    Weekly, Eco data, market condition, bubble analysis
    """

    bubble_stage = models.CharField(
        max_length=20, help_text='Market fair value',
        choices=(
            ('birth', 'The birth of a boom - some sector, other sector down'),
            ('breed', 'The breed of a bubble - rate low, credit grow, company increase profit'),
            ('new_era', 'Everyone buy new ara - always go up, valuation standard abandon'),
            ('distress', 'Financial distress - insider cash out, excess leverage, fraud detected'),
            ('scare', 'Financial scare - investor scare, no longer trade in market'),
        ),
    )
    pass



# todo: add another eco data checklist for eco
