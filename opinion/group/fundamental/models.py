import datetime
from django.db import models


class StockIndustry(models.Model):
    """
    Industry analysis, update season after earning or enter position
    """
    symbol = models.CharField(max_length=10)
    date = models.DateField(default=datetime.datetime.now)

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


class StockFundamental(models.Model):
    """
    Simple fundamental analysis, micro valuation for stock, weekly update
    """
    # micro valuation
    symbol = models.CharField(max_length=6)
    date = models.DateField(default=datetime.datetime.now)

    # unique data
    unique_together = (('symbol', 'date'),)

    # Strong-Form Hypothesis
    mean_rank = models.FloatField(default=3, help_text='Fundamental Mean Rank')
    ownership_activity = models.CharField(
        max_length=20,
        choices=(('selling', 'Selling'), ('holding', 'Holding'), ('buying', 'Buying')),
        help_text='Ownership net activity - 45 days'
    )
    insider_trade = models.CharField(
        max_length=20, help_text='Insider trades - 30 days', default='holding',
        choices=(('selling', 'Selling'), ('holding', 'Holding'), ('buying', 'Buying')),
    )
    guru_trade = models.CharField(
        max_length=20, help_text='Guru trades - 90 days', default='holding',
        choices=(('selling', 'Selling'), ('holding', 'Holding'), ('buying', 'Buying')),
    )
    short_interest = models.CharField(
        max_length=20, help_text='Short interest - 0.5 month', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    risk = models.CharField(
        max_length=20, help_text='Risk', default='middle',
        choices=(('low', 'Low'), ('middle', 'Middle'), ('high', 'High'))
    )

    # target price
    target_price_max = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Max Target Price'
    )
    target_price_mean = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Mean Target Price'
    )
    target_price_min = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Min Target Price'
    )


class UnderlyingArticle(models.Model):
    """
    Primary use for tracking story telling or irrational move
    """
    # Semi-Strong Form
    symbol = models.CharField(max_length=20)
    date = models.DateField(default=datetime.datetime.now)
    unique_together = (('symbol', 'date'),)

    category = models.CharField(
        max_length=20, help_text='Type of this market story',
        choices=(('title', 'Big title'), ('story', 'Story telling'), ('news', 'Simple News'))
    )

    article_name = models.CharField(
        max_length=200, help_text='Name of the story, news, title'
    )
    article_story = models.CharField(
        max_length=20, help_text='Current state of article telling',
        choices=(
            ('good90', 'Good story 90% chance, 88% follow'),
            ('good30', 'Good story 30% chance, 78% follow'),
            ('bad90', 'Bad story 90% chance, 38% follow'),
            ('bad30', 'Bad story 30% chance, 7% follow')
        )
    )
    period_state = models.CharField(
        max_length=20, help_text='Current state of story telling',
        choices=(
            ('latest', 'Latest 1 or 2 days'),
            ('recent', 'Recent 1 week'),
            ('forget', 'Pass 2 weeks')
        )
    )
    fundamental_effect = models.BooleanField(
        default=True, help_text='This article have fundamental effect?'
    )
    rational = models.BooleanField(
        default=True, help_text='This story is rational? yes or no, you only follow'
    )
    blind_follow = models.BooleanField(
        default=True, help_text='Follow story? Short term follow? Long term reverse?'
    )
    reverse_effect = models.BooleanField(
        default=True, help_text='Is this bad news as good news? good news as bad news?'
    )

    # news effect price probability
    bull_chance = models.FloatField(default=33, help_text='Chance of bull move by this news')
    range_chance = models.FloatField(default=34, help_text='Chance of range move by this news')
    bear_chance = models.FloatField(default=33, help_text='Chance of bear move by this news')
