from django.db import models


class IndustryOpinion(models.Model):
    """
    Industry analysis, update season after earning or enter position
    """
    symbol = models.CharField(max_length=10)
    date = models.DateField()

    # unique data
    unique_together = (('symbol', 'date'),)

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

    # unique data
    unique_together = (('symbol', 'date'),)

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

