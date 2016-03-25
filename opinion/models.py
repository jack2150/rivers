from django.db import models
from statement.models import Position


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


class IndustryOpinion(models.Model):
    """
    Industry analysis, update season after earning or enter position
    """
    symbol = models.CharField(max_length=10)
    date = models.DateField()
    sector = models.CharField(max_length=20)  # main
    industry = models.CharField(max_length=20)  # sub

    # industry index comparison
    index_trend = models.CharField(
        max_length=10,
        choices=(('bearish', 'Bearish'), ('neutral', 'Neutral'), ('bullish', 'Bullish')),
        help_text='Industry index trend'
    )
    isolate = models.BooleanField(
        default=False,
        help_text='Company follow industry or stand out'
    )
    risk_diff = models.CharField(
        max_length=10,
        choices=(('lower', 'Lower'), ('range', 'Range'), ('higher', 'Higher')),
        help_text='Risk different with other company'
    )

    # business cycle peak
    # financial: bank, equity, bond
    # durables: cars, personal computers, refrigerators
    # goods: heavy equipment, machine tool, and airplane
    # industry: oil, metals, and timber, raw materials
    # staples: pharmaceuticals, food, and beverages
    biz_cycle = models.CharField(
        max_length=20, blank=True, default='',
        choices=(
            ('financial', 'Financial'), ('durables', 'Durables'), ('goods', 'Goods'),
            ('industry', 'Industry'), ('staples', 'Staples'), ('', 'Unknown')
        ),
        help_text='Current business cycle peak industry'
    )
    cs_trend = models.CharField(
        max_length=10, blank=True,
        choices=(('lower', 'Lower'), ('range', 'Range'), ('higher', 'Higher')),
        help_text='Consumer sentiment trend'
    )

    # structural change
    structural_chg = models.CharField(
        max_length=20, blank=True, default='',
        choices=(
            ('demographic', 'Demographic'), ('lifestyle', 'Lifestyle'),
            ('technology', 'Technology'), ('regulation', 'Regulation'), ('', 'No change'),
        ),
        help_text='Industry structural change'
    )

    # industry life cycle
    # pioneer: biz start
    # accelerate: can grow more than 100% profit
    # mature: grow something like 20%
    # stable: little change in profit
    # decline: low profit or losses
    life_cycle = models.CharField(
        max_length=20, blank=True, default='',
        choices=(
            ('pioneer', 'Pioneer'), ('accelerate', 'Accelerate'), ('mature', 'Mature'),
            ('stable', 'Stable'), ('decline', 'Decline'), ('', 'Unknown')
        ),
        help_text='Industry life cycle'
    )

    # Industry competition
    competition = models.CharField(
        max_length=20, blank=True,
        choices=(
            ('rivalry', 'Rivalry'), ('new_entry', 'New entry'), ('more_product', 'More product'),
            ('buyer_bargain', 'Buyer bargain'), ('supplier_bargain', 'Supplier bargain'),
            ('', 'Similar')
        ),
        default='',
        help_text='Industry competition'
    )

    # valuation vs industry
    industry_pe = models.CharField(
        max_length=10,
        choices=(('lower', 'Lower'), ('range', 'Range'), ('higher', 'Higher')),
        help_text='Morning p/e comparison'
    )
    industry_rank = models.CharField(
        max_length=10,
        choices=(('lower', 'Lower'), ('range', 'Range'), ('higher', 'Higher')),
        help_text='Zack industry rank'
    )
    industry_fa = models.CharField(
        max_length=10,
        choices=(('worst', 'Worst'), ('average', 'Average'), ('better', 'Better')),
        help_text='Industry fundamental'
    )

    # fair value
    fair_value = models.CharField(
        max_length=10,
        choices=(('lower', 'Lower'), ('range', 'Range'), ('higher', 'Higher')),
        help_text='Industry fair value'
    )


class FundamentalOpinion(models.Model):
    """
    Simple fundamental analysis, micro valuation for stock, weekly update
    """
    # micro valuation
    symbol = models.CharField(max_length=6)
    date = models.DateField()

    # Strong-Form Hypothesis
    mean_rank = models.FloatField(default=3, help_text='Mean Analyst Recommendation')

    ownership_activity = models.CharField(
        max_length=20,
        choices=(('selling', 'Selling'), ('holding', 'Holding'), ('buying', 'Buying')),
        help_text='Ownership net activity - 45 days'
    )
    insider_trade = models.CharField(
        max_length=20,
        choices=(('selling', 'Selling'), ('holding', 'Holding'), ('buying', 'Buying')),
        help_text='Insider trades - 30 days'
    )
    guru_trade = models.CharField(
        max_length=20,
        choices=(('selling', 'Selling'), ('holding', 'Holding'), ('buying', 'Buying')),
        help_text='Guru trades - 90 days'
    )
    short_interest = models.CharField(
        max_length=20,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='Short interest'
    )

    # Semi strong-Form Hypothesis
    # http://markets.ft.com/research/Markets/Tearsheets/Forecasts?s=MSFT:NSQ
    earning_surprise = models.CharField(
        max_length=20, blank=True, default='',
        choices=(('negative', 'Negative'), ('no-surprise', 'No-surprise'), ('positive', 'Positive')),
        help_text='Earning surprise'
    )
    earning_grow = models.CharField(
        max_length=20,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='EPS Growth Estimate'
    )
    dividend_grow = models.CharField(
        max_length=20, blank=True,
        choices=(
            ('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase'),
            ('', 'No dividend')
        ),
        default='',
        help_text='Dividend Growth Estimate'
    )
    # http://markets.ft.com/research/Markets/Tearsheets/Forecasts?s=AIG:NYQ
    target_price_max = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Max Target Price'
    )
    target_price_mean = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Mean Target Price'
    )
    target_price_min = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Min Target Price'
    )

    # Micro valuation analysis
    # Discounted Cash Flow Model
    dcf_value = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text='Discounted cash flow model'
    )

    # Earnings Multiplier
    pe_ratio_trend = models.CharField(
        max_length=10,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
        help_text='Price earnings multiplier'
    )
    div_yield_trend = models.CharField(
        max_length=10,
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase'),),
        help_text='Dividend yield per share'
    )
    valuation = models.CharField(
        max_length=10,
        choices=(('expensive', 'Expensive'), ('normal', 'Normal'), ('cheap', 'Cheap')),
        help_text='TD Valuation'
    )


class WeekdayOpinion(models.Model):
    """
    Basic stock movement and news/information, daily update
    """
    symbol = models.CharField(max_length=6)
    date = models.DateField()
    close_price = models.DecimalField(max_digits=10, decimal_places=2)

    # new information
    new_info_impact = models.BooleanField(
        default=False, help_text='New information that affect stock valuation'
    )
    new_info_move = models.CharField(
        max_length=20, blank=True,
        choices=(('bullish', 'Bullish'), ('neutral', 'Neutral'),
                 ('bearish', 'Bearish'), ('', 'None')),
        default='',
        help_text='New information cause price movement'
    )
    new_info_desc = models.TextField(blank=True, null=True)

    # options & volatility
    today_iv = models.FloatField(help_text='Today Implied Volatility')
    iv_rank = models.CharField(
        max_length=20,
        choices=(('below_33', 'Below 33%'), ('34_to_66', '34% to 66%'), ('above_66', 'Above 67%')),
        help_text='Current IV Percentile Rank'
    )
    hv_rank = models.CharField(
        max_length=20,
        choices=(('below_33', 'Below 33%'), ('34_to_66', '34% to 66%'), ('above_66', 'Above 67%')),
        help_text='Current HV Percentile Rank'
    )

    put_call_ratio = models.FloatField(help_text='Today Put/Call Ratio')

    # identify spread is buy or sell, check price and market range, lower is sell, higher is buy
    today_biggest = models.CharField(
        max_length=20, blank=True, default='',
        choices=(('bullish', 'Bull Spread'), ('neutral', 'Neutral Spread'),
                 ('bearish', 'Bear Spread'), ('', 'None')),
        help_text='Option times & sales more than 100 quantity (identify: price and market range)'
    )

    sizzle_index = models.FloatField(
        default=0, help_text='unusually options volume as compared to previous 5 day options volume'
    )

    # technical analysis
    last_5day_return = models.FloatField(
        default=0, help_text='Last 5 days long holding return in %'
    )
    consecutive_move = models.CharField(
        max_length=20, default='un-change',
        choices=(('up', 'Move up'), ('down', 'Move down'), ('no-change', 'No-change')),
        help_text='Latest statistic consecutive move, example: +++ or --'
    )
    unusual_volume = models.CharField(
        max_length=20, default='', blank=True,
        choices=(('bullish', 'Bullish'), ('bearish', 'Bearish'), ('', 'None')),
        help_text='Stock unusual trading volume'
    )
    moving_avg200x50 = models.CharField(
        max_length=20, blank=True, default='',
        choices=(('bullish', 'Bullish'), ('neutral', 'Neutral'),
                 ('bearish', 'Bearish'), ('', 'None')),
        help_text='200/50-days Moving average moving same direction?'
    )
    weekend_effect = models.BooleanField(
        default=False,
        help_text='Weekend effect happen (large move Friday, small move Monday)?'
    )

    # price movement
    previous_short_trend = models.CharField(
        choices=(('bullish', 'Bullish'), ('neutral', 'Neutral'), ('bearish', 'Bearish')),
        max_length=20, help_text='Previous short-term price movement'
    )
    current_short_trend = models.CharField(
        choices=(('bullish', 'Bullish'), ('neutral', 'Neutral'), ('bearish', 'Bearish')),
        max_length=20, help_text='Current short-term price movement'
    )
    previous_long_trend = models.CharField(
        choices=(('bullish', 'Bullish'), ('neutral', 'Neutral'), ('bearish', 'Bearish')),
        max_length=20, help_text='Previous long-term price movement'
    )
    current_long_trend = models.CharField(
        choices=(('bullish', 'Bullish'), ('neutral', 'Neutral'), ('bearish', 'Bearish')),
        max_length=20, help_text='Current long-term price movement'
    )

    # position analysis
    position_stage = models.CharField(
        max_length=20, default='un-change',
        choices=(('best', 'Best'), ('better', 'Better'),
                 ('un-change', 'Un-change'), ('danger', 'Danger'), ('worst', 'Worst')),
        help_text='Position stage'
    )
    position_hold = models.BooleanField(
        default=True, help_text='Continue hold position'
    )
    position_action = models.CharField(
        max_length=20, default='', blank=True,
        choices=(('close', 'Close'), ('prepare_close', 'Prepare close'),
                 ('adjust', 'Adjust'), ('no-action', 'No-action')),
        help_text='Action to be taken'
    )

    # others
    short_squeeze = models.BooleanField(default=False, help_text='Short squeeze possible?')
    others = models.TextField(
        null=True, blank=True, help_text='Extra note or attention write here'
    )


class PositionOpinion(models.Model):
    """
    Position opinion, only create when enter new position
    """
    symbol = models.CharField(max_length=6)
    date = models.DateField()

    risk_profile = models.CharField(
        max_length=20, choices=(('low', 'Low'), ('medium', 'Medium'), ('high', 'High')),
        help_text='Risk you willing to take for this position'
    )
    bp_effect = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Buying power effect to portfolio'
    )
    max_profit = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Max profit for this position'
    )
    max_loss = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Max loss for this position'
    )
    size = models.IntegerField(
        default=0, help_text='Trade quantity'
    )
    strategy = models.CharField(
        max_length=50, help_text='Valid strategy for current market, movement, and volatility'
    )
    spread = models.CharField(
        max_length=10,
        choices=(('credit', 'Credit'), ('debit', 'Debit')),
        default='debit',
        help_text='Credit or debit spread'
    )
    optionable = models.BooleanField(default=False, help_text='Option position?')

    enter_date = models.DateField()
    exit_date = models.DateField(null=True, blank=True)
    dte = models.IntegerField(
        null=True, blank=True,
        help_text='For option strategy only, make sure dte long enough.'
    )

    # trade signal
    price_movement = models.CharField(
        max_length=20,
        choices=(('bullish', 'Bullish'), ('neutral', 'Neutral'), ('bearish', 'Bearish')),
        help_text='Profit price movement'
    )
    target_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Rational expected target price'
    )

    # event check
    event_trade = models.BooleanField(default=False, help_text='Event signal trade?')
    event_period = models.CharField(
        max_length=20, blank=True, default='',
        choices=(
            ('earning', 'Earning'), ('dividend', 'Dividend'), ('split', 'Split'),
            ('announcement', 'Announcement'), ('seasonal', 'Seasonal events'),
            ('multiple', 'Multiple events'), ('', 'None')
        ),
        help_text='Event happen between holding period'
    )

    # extra note
    description = models.TextField(null=True, blank=True)


class CloseOpinion(models.Model):
    """
    Position closing opinion, create only when close
    """
    symbol = models.CharField(max_length=6)
    date = models.DateField()

    auto_trigger = models.BooleanField(
        default=False, help_text='Create day or gtc order for auto trigger'
    )

    condition = models.CharField(
        max_length=20, default='stat_change',
        choices=(('expire', 'Expire'), ('max_risk', 'Reach max risk'),
                 ('profit_taken', 'Profit taken'), ('stat_change', 'Statistic change')),
        help_text='Condition met when you decide to close position',
    )

    result = models.CharField(
        max_length=20, default='breakeven',
        choices=(('profit', 'Profit'), ('breakeven', 'Breakeven'), ('loss', 'Loss')),
        help_text='Position close result',
    )

    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0,
        help_text='Position close profit/loss total amount',
    )
    stock_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0,
        help_text='Underlying price when closing position'
    )
    timing = models.CharField(
        max_length=20,
        choices=(('good', 'Good'), ('normal', 'Normal'), ('bad', 'Bad')),
        help_text='Exit timing opinion',
        default='normal'
    )
    wait = models.BooleanField(
        default=False, help_text='Is tomorrow a better day to close?'
    )

    others = models.TextField(null=True, blank=True)


class BehaviorOpinion(models.Model):
    """
    Emotion and trading condition analysis, daily update
    """
    date = models.DateField()

    prospect_theory = models.BooleanField(
        default=True, help_text='Hold on to losers too long and sell winners too soon.'
    )
    belief_perseverance = models.BooleanField(
        default=True, help_text='Opinion keep too long not update; skeptical/misinterpret new info'
    )
    anchoring = models.BooleanField(
        default=True, help_text='Wrong estimate initial stock value with adjustment'
    )
    over_confidence = models.BooleanField(
        default=True, help_text='Overestimate growth forecast, overemphasize '
                                'good news and ignore negative news'
    )
    confirmation_bias = models.BooleanField(
        default=True,
        help_text='Do you believe your positions is good, find news supports that opinions but mis-value'
    )
    self_attribution = models.BooleanField(
        default=True, help_text='Do you blame failure on bad luck, or overestimate your research'
    )
    noise_trading = models.BooleanField(
        default=True, help_text='Using nonprofessionals with no special information to trade'
    )
    hindsight_bias = models.BooleanField(
        default=True, help_text='Do you think that you can predict better than analysts?'
    )
    escalation_bias = models.BooleanField(
        default=True, help_text='Do you put more money because of failure?'
    )
    serious_analysis = models.BooleanField(
        default=False, help_text='Do you seriously look for the bad news on the valuation?'
    )
