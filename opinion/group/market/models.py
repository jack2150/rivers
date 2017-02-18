import datetime
from django.db import models


class MarketReview(models.Model):
    """
    macro valuation, Weekly update
    """
    date = models.DateField(
        help_text='Monthly',
        default=datetime.datetime.now
    )

    # eco stage
    bubble_stage = models.CharField(
        max_length=20, help_text='Market fair value', default='new_era',
        choices=(
            ('birth', 'The birth of a boom - some sector, other sector down'),
            ('breed', 'The breed of a bubble - rate low, credit grow, company increase profit'),
            ('new_era', 'Everyone buy new ara - always go up, valuation standard abandon'),
            ('distress', 'Financial distress - insider cash out, excess leverage, fraud detected'),
            ('scare', 'Financial scare - investor scare, no longer trade in market'),
        ),
    )
    market_scenario = models.CharField(
        max_length=20, help_text='Inflation, Interest Rates, and Stock Prices', default='positive',
        choices=(('very_negative', 'Very Negative - interest+, inflation+, stock-, cash-'),
                 ('midly_negative', 'Midly Negative - interest+, inflation+, stock-, cash+'),
                 ('positive', 'Positive - rate+, inflation+, stock+, sale+'))
    )

    # major economics indicator
    cli_trend = models.CharField(
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        max_length=20, help_text='Composite leading indicator', default='range'
    )
    bci_trend = models.CharField(
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        max_length=20, help_text='Business Cycle Indicator', default='range'
    )

    # economics data
    m2_supply = models.CharField(
        max_length=20, help_text='M2 Money supply', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    gdp = models.CharField(
        max_length=20, help_text='GDP & Real GDP', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    cpi = models.CharField(
        max_length=20, help_text='Consumer Price Index', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    ppi = models.CharField(
        max_length=20, help_text='Producer Price Index', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    cc_survey = models.CharField(
        max_length=20, help_text='Consumer Confidence Survey', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    employ = models.CharField(
        max_length=20, help_text='Employment status', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    retail_sale = models.CharField(
        max_length=20, help_text='US Retail Sales', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    house_start = models.CharField(
        max_length=20, help_text='Housing Starts', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    industry = models.CharField(
        max_length=20, help_text='Manufacturing Production Index', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    biz_inventory = models.CharField(
        max_length=20, help_text='Total Business Inventories', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    startup = models.CharField(
        max_length=20, help_text='Startup Activity', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    week_earning = models.CharField(
        max_length=20, help_text='Average Weekly Earnings', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    currency_strength = models.CharField(
        max_length=20, help_text='Foreign Exchange Indicators', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    interest_rate = models.CharField(
        max_length=20, help_text='Interest Rates Indicators', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    corp_profit = models.CharField(
        max_length=20, help_text='Corporate Profits After Tax', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    trade_deficit = models.CharField(
        max_length=20, help_text='Trade Deficit', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )

    # most important
    monetary_policy = models.TextField(
        null=True, blank=True, help_text='Monetary policy simple explanation'
    )
    month_commentary = models.TextField(
        null=True, blank=True, help_text='Write down what important next month'
    )


class MarketMovement(models.Model):
    """
    market move, economics calendar, special market news, update daily
    """
    date = models.DateField(unique=True, default=datetime.datetime.now, help_text='BDays')

    # support and resistant
    support = models.FloatField(default=0, help_text='S&P 500 Support Weekly')
    resistant = models.FloatField(default=0, help_text='S&P 500 Resistant Weekly')
    volume = models.CharField(
        max_length=20, default='average',
        choices=(('tiny', 'Tiny'), ('average', 'Average'), ('huge', 'Huge')),
    )
    vix = models.CharField(
        max_length=20, help_text='Market volatility /VX or VIX', default='normal',
        choices=(('low', 'Low'), ('normal', 'Normal'), ('high', 'High')),
    )

    # core technical weekly
    technical_rank = models.IntegerField(
        help_text='S&P 500 technical rank', default=3,
        choices=((1, 'Strong sell'), (2, 'Sell'), (3, 'Hold'), (4, 'Buy'), (5, 'Strong buy'))
    )

    # section: price and volume
    # down theory for market
    dow_phase = models.CharField(
        max_length=20, help_text='Dow theory phase /YM', default='trend',
        choices=(('accumulate', 'Accumulate'), ('trend', 'Trend'), ('distribute', 'Distribute')),
    )
    dow_movement = models.CharField(
        max_length=20, help_text='Dow theory movement /YM', default='bullish',
        choices=(('bullish', 'Bullish'), ('bearish', 'Bearish'), ('medium_swing', 'Medium swing'),
                 ('short_swing', 'Short swing')),
    )

    # economics calendar
    market_indicator = models.IntegerField(default=0)
    extra_attention = models.IntegerField(default=0)
    key_indicator = models.IntegerField(default=0)
    special_news = models.BooleanField(default=False)

    def __unicode__(self):
        return 'MarketMovement {date}'.format(date=self.date)


class CommodityMovement(models.Model):
    market_movement = models.ForeignKey(MarketMovement)
    trading_hour = models.CharField(
        max_length=20, help_text='Trading hours', default='open',
        choices=(('open', 'Open'), ('mid', 'Mid'), ('close', 'Close')),
    )
    unique_together = (('market_movement', 'trading_hour'),)

    # commodity
    currency = models.CharField(
        max_length=20, help_text='US Dollar /DX', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull'))
    )
    bond = models.CharField(
        max_length=20, help_text='Bond AGG & TLT', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    energy = models.CharField(
        max_length=20, help_text='Energy XLE', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    metal = models.CharField(
        max_length=20, help_text='Metal GLD & SLV', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    grain = models.CharField(
        max_length=20, help_text='Agriculture DBA (Grain & Soft)', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )


class WorldMovement(models.Model):
    market_movement = models.ForeignKey(MarketMovement)
    trading_hour = models.CharField(
        max_length=20, help_text='Trading hours', default='open',
        choices=(('open', 'Open'), ('mid', 'Mid'), ('close', 'Close')),
    )
    unique_together = (('market_movement', 'trading_hour'),)

    # major country
    uk = models.CharField(
        max_length=20, help_text='UK index movement', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    germany = models.CharField(
        max_length=20, help_text='Germany index movement', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    russia = models.CharField(
        max_length=20, help_text='Russia index movement', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    china = models.CharField(
        max_length=20, help_text='China index movement', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    japan = models.CharField(
        max_length=20, help_text='Japan index movement', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    brazil = models.CharField(
        max_length=20, help_text='Brazil movement', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )

    # world region summary
    euro = models.CharField(
        max_length=20, help_text='Euro market movement', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    asia = models.CharField(
        max_length=20, help_text='Asia market movement', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    america = models.CharField(
        max_length=20, help_text='America market movement', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    africa = models.CharField(
        max_length=20, help_text='Africa market movement', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )


class SectorMovement(models.Model):
    market_movement = models.ForeignKey(MarketMovement)
    trading_hour = models.CharField(
        max_length=20, help_text='Trading hours', default='open',
        choices=(('open', 'Open'), ('mid', 'Mid'), ('close', 'Close')),
    )
    unique_together = (('market_movement', 'trading_hour'),)

    consumer_disc = models.CharField(
        max_length=20, help_text='Consumer Discretionary sector movement (XLY)', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    consumer_staples = models.CharField(
        max_length=20, help_text='Consumer staples sector movement (XLP)', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    energy = models.CharField(
        max_length=20, help_text='Energy sector movement (XLE)', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    financial = models.CharField(
        max_length=20, help_text='Financial sector movement (XLF)', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    health_care = models.CharField(
        max_length=20, help_text='Health care sector movement (XLV)', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    industry = models.CharField(
        max_length=20, help_text='Industry sector movement (XLI)', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    material = models.CharField(
        max_length=20, help_text='Material sector movement (XLB)', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    real_estate = models.CharField(
        max_length=20, help_text='Real estate sector movement (XLRE)', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    technology = models.CharField(
        max_length=20, help_text='Technology sector movement (XLK)', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )
    utility = models.CharField(
        max_length=20, help_text='Utility sector movement (XLU)', default='range',
        choices=(('bear', 'Bear'), ('range', 'Range'), ('bull', 'Bull')),
    )


class MarketSentiment(models.Model):
    """
    Popular market indicator, weekly update
    """
    date = models.DateField(default=datetime.datetime.now)

    # section: Contrary-Opinion Rules
    # negative: borrow cash to invest, positive: sell share for cash
    fund_cash_ratio = models.CharField(
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        max_length=20, help_text='Mutual fund cash ratio', default='range'
    )

    # credit balance lower: investor buy, higher: investor sell
    credit_balance = models.CharField(
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        max_length=20, help_text='Market credit balance', default='range'
    )

    # from cnn money
    sentiment_index = models.CharField(
        choices=(('greed', 'Greed'), ('neutral', 'Neutral'), ('fear', 'Fear')),
        max_length=20, help_text='Fear & Greed index', default='neutral'
    )  # greek: move up, fear: move down
    put_call_ratio = models.CharField(
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        max_length=20, help_text='Market put call ratio', default='range'
    )  # market put call buy ratio, higher: more call, bull, lower: more put, bear
    market_momentum = models.CharField(
        choices=(('greed', 'Greed'), ('neutral', 'Neutral'), ('fear', 'Fear')),
        max_length=20, help_text='Market momentum', default='neutral'
    )
    junk_bond_demand = models.CharField(
        choices=(('greed', 'Greed'), ('neutral', 'Neutral'), ('fear', 'Fear')),
        max_length=20, help_text='Junk bond demand', default='neutral'
    )
    price_strength = models.CharField(
        choices=(('greed', 'Greed'), ('neutral', 'Neutral'), ('fear', 'Fear')),
        max_length=20, help_text='Price strength', default='neutral'
    )
    safe_heaven_demand = models.CharField(
        choices=(('greed', 'Greed'), ('neutral', 'Neutral'), ('fear', 'Fear')),
        max_length=20, help_text='Safe heaven demand', default='neutral'
    )
    market_volatility = models.CharField(
        choices=(('greed', 'Greed'), ('neutral', 'Neutral'), ('fear', 'Fear')),
        max_length=20, help_text='Market volatility', default='neutral'
    )

    # lower: investor sell, higher: investor buy
    investor_sentiment = models.CharField(
        choices=(('bearish', 'Bearish'), ('neutral', 'Neutral'), ('bullish', 'Bullish')),
        max_length=20, help_text='Investor sentiment', default='neutral'
    )

    # s&p 500 share change,
    futures_trader = models.CharField(
        choices=(('bearish', 'Bearish'), ('neutral', 'Neutral'), ('bullish', 'Bullish')),
        max_length=20, help_text='CFTC S&P 500 trader', default='neutral'
    )

    # section: smart money
    # bond conf index, higher: invest in bond, lower: invest in stock
    confidence_index = models.CharField(
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        max_length=20, help_text='Confidence Index', default='range'
    )

    # t-bill eurodollar spread,
    # higher: money into t-bill, stock down,
    # lower: money out t-bill, stock up
    ted_spread = models.CharField(
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        max_length=20, help_text='Ted spread', default='range'
    )

    # investor borrow more: higher, stock up; borrow less: lower, stock down
    margin_debt = models.CharField(
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        max_length=20, help_text='Margin debt', default='range'
    )

    # section: market momentum
    # Breadth of Market: high, more advance price, stock up; low, more decline price, stock down
    market_breadth = models.CharField(
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        max_length=20, help_text='Breadth of Market', default='range'
    )

    # below 20: oversold, above: 80 overbought
    ma200day_pct = models.CharField(
        choices=(('overbought', 'Overbought'), ('fair_value', 'Fair value'), ('oversold', 'Oversold')),
        max_length=20, help_text='% of S&P 500 Stocks Above 200-Day Moving Average', default='fair_value'
    )

    # $trin, Short-Term Trading Index: overbought: sell, oversold: buy
    arms_index = models.CharField(
        choices=(('overbought', 'Overbought'), ('fair_value', 'Fair value'), ('oversold', 'Oversold')),
        max_length=20, help_text='Short-Term Trading Arms Index', default='fair_value'
    )

    # market fair value, undervalue: buy, overvalue: sell
    fair_value_trend = models.CharField(
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        max_length=20, help_text='Market fair value', default='range'
    )


class MarketWeekTechnical(models.Model):
    market_sentiment = models.OneToOneField(MarketSentiment)

    cyclical = models.CharField(
        choices=(('bull', 'Bull'), ('neutral', 'Neutral'), ('bear', 'Bear')),
        max_length=20, help_text='CYCLICAL TREND INDEX', default='neutral'
    )
    momentum = models.CharField(
        choices=(('bull', 'Bull'), ('neutral', 'Neutral'), ('bear', 'Bear')),
        max_length=20, help_text='MOMENTUM INDEX', default='neutral'
    )
    sentiment = models.CharField(
        choices=(('bull', 'Bull'), ('neutral', 'Neutral'), ('bear', 'Bear')),
        max_length=20, help_text='SENTIMENT INDEX', default='neutral'
    )
    strength = models.CharField(
        choices=(('bull', 'Bull'), ('neutral', 'Neutral'), ('bear', 'Bear')),
        max_length=20, help_text='CYCLICAL TREND INDEX', default='neutral'
    )
    summary = models.TextField(
        default='', blank=True, null=True,help_text='On the edge summary'
    )


class MarketWeekReport(models.Model):
    market_sentiment = models.ForeignKey(MarketSentiment)

    source = models.CharField(
        choices=(
            ('web', 'Web or Video'),
            ('schwab', 'Charles Schwab'),
            ('jpm', 'JP Morgan'),
            ('blk', 'Black Rock'),
            ('tda', 'TD Ameritrade'),
        ),
        max_length=20, help_text='Article source', default=''
    )
    expect = models.CharField(
        choices=(('bull', 'Bull'), ('neutral', 'Neutral'), ('bear', 'Bear')),
        max_length=20, help_text='Expect market direction', default='neutral'
    )
    comment = models.TextField(
        default='', blank=True, null=True, help_text='Commentary'
    )


class MarketArticle(models.Model):
    date = models.DateField(default=datetime.datetime.now)
    link = models.CharField(max_length=2000, help_text='article source')
    name = models.CharField(max_length=500, help_text='article title')
    category = models.CharField(
        help_text='Type of article', max_length=20, default='review',
        choices=(('review', 'Review'), ('analysis', 'Analysis'), ('general', 'General'))
    )
    chance = models.CharField(
        help_text='Chance of happen', max_length=20, default='low',
        choices=(('low', 'Low'), ('medium', 'Medium'), ('high', 'High'))
    )
    key_point = models.TextField(help_text='Main point & extra attention')

















