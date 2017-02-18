import datetime
from django.db import models

from opinion.group.report.models import ReportEnter


class StockFundamental(models.Model):
    """
    Simple fundamental analysis, micro valuation for stock, weekly update
    """
    report = models.OneToOneField(ReportEnter, null=True, blank=True)

    # Strong-Form Hypothesis
    # rank
    mean_rank = models.FloatField(default=3, help_text='Fundamental Mean Rank')
    accuracy = models.IntegerField(default=50, help_text='Upgrade/downgrade accuracy')
    rank_change = models.CharField(
        max_length=20, help_text='Latest rank change', default='upgrade',
        choices=(('upgrade', 'Upgrade'), ('hold', 'Hold'), ('downgrade', 'Downgrade')),
    )
    change_date = models.DateField(null=True, help_text='Latest rank change date')
    risk = models.CharField(
        max_length=20, help_text='From S&P report', default='middle',
        choices=(('low', 'Low'), ('middle', 'Middle'), ('high', 'High'))
    )

    # target price
    tp_max = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Max Target Price'
    )
    tp_mean = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Mean Target Price'
    )
    tp_min = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Min Target Price'
    )

    # ownership change
    ownership_activity = models.CharField(
        max_length=20,
        choices=(('selling', 'Selling'), ('holding', 'Holding'), ('buying', 'Buying')),
        help_text='Ownership net activity - 45 days'
    )
    ownership_date = models.DateField(null=True, help_text='Latest short interest date')
    insider_trade = models.CharField(
        max_length=20, help_text='Insider trades - 30 days', default='holding',
        choices=(('selling', 'Selling'), ('holding', 'Holding'), ('buying', 'Buying')),
    )
    insider_date = models.DateField(null=True, help_text='Latest short interest date')
    short_interest = models.CharField(
        max_length=20, help_text='Short interest - 0.5 month', default='range',
        choices=(('decrease', 'Decrease'), ('range', 'Range'), ('increase', 'Increase')),
    )
    short_date = models.DateField(null=True, help_text='Latest short interest date')
    guru = models.TextField(blank=True, null=True, help_text='Latest guru trade')


class StockIndustry(models.Model):
    """
    Industry analysis, update season after earning or enter position
    """
    report = models.OneToOneField(ReportEnter, null=True, blank=True)

    # industry overall
    direction = models.CharField(
        max_length=20, default=None, blank=True, null=True,
        help_text='Zack industry chart direction 3 months',
        choices=(('bull', 'Bull'), ('neutral', 'Neutral'), ('bear', 'Bear')),
    )
    isolate = models.BooleanField(default=False, help_text='Stock price with index?')
    industry_rank = models.CharField(
        max_length=20, default='middle', help_text='Zack industry rank',
        choices=(('top', 'Top'), ('middle', 'Middle'), ('bottom', 'Bottom')),
    )
    sector_rank = models.CharField(
        max_length=20, default='middle', help_text='Zack industry rank',
        choices=(('top', 'Top'), ('middle', 'Middle'), ('bottom', 'Bottom')),
    )

    # stock vs peer
    stock_rank = models.CharField(
        max_length=20, default='middle', help_text='Zack stock rank vs peer',
        choices=(('better', 'Better'), ('same', 'Same'), ('lower', 'Lower')),
    )
    stock_growth = models.CharField(
        max_length=20, default='middle', help_text='Zack stock rank vs peer',
        choices=(('better', 'Better'), ('same', 'Same'), ('lower', 'Lower')),
    )
    stock_financial = models.CharField(
        max_length=20, default='middle', help_text='Zack stock rank vs peer',
        choices=(('better', 'Better'), ('same', 'Same'), ('lower', 'Lower')),
    )


class UnderlyingArticle(models.Model):
    """
    Primary use for tracking story telling or irrational move
    """
    report = models.OneToOneField(ReportEnter, null=True, blank=True)

    # Semi-Strong Form
    category = models.CharField(
        max_length=20, help_text='Type of this market story', default='title',
        choices=(('title', 'Big title'), ('story', 'Story telling'), ('news', 'Simple News'))
    )
    article_name = models.CharField(
        default='', max_length=200, help_text='Name of the story, news, title'
    )
    article_story = models.CharField(
        max_length=20, help_text='Current state of article telling', default='good30',
        choices=(
            ('good90', 'Good story 90% chance, 88% follow'),
            ('good30', 'Good story 30% chance, 78% follow'),
            ('bad90', 'Bad story 90% chance, 38% follow'),
            ('bad30', 'Bad story 30% chance, 7% follow')
        )
    )
    period_state = models.CharField(
        max_length=20, help_text='Current state of story telling', default='latest',
        choices=(
            ('latest', 'Latest 1 or 2 days'),
            ('recent', 'Recent 1 week'),
            ('forget', 'Pass 2 weeks')
        )
    )

    # news summary
    news_rank = models.CharField(
        max_length=20, default=None, blank=True, null=True,
        help_text='Benzinga pro news rank 14 days',
        choices=(('good', 'Good'), ('neutral', 'Neutral'), ('bad', 'Bad')),
    )
    news_effect = models.CharField(
        max_length=20, default='neutral', help_text='14 days price move with news',
        choices=(('bull', 'Bull'), ('neutral', 'Neutral'), ('bear', 'Bear')),
    )

    # behavior opinion
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
