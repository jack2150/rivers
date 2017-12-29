import datetime
from django.db import models
from base.ufunc import UploadRenameImage
from opinion.group.report.models import UnderlyingReport


class StockProfile(models.Model):
    """
    Overall stock profile
    """
    report = models.OneToOneField(UnderlyingReport, null=True, blank=True)

    def __unicode__(self):
        return 'StockProfile <{symbol}>'.format(symbol=self.report.symbol)


class UnderlyingArticle(models.Model):
    """
    Primary use for tracking story telling or irrational move
    """
    report = models.OneToOneField(UnderlyingReport, null=True, blank=True)

    # Semi-Strong Form
    category = models.CharField(
        max_length=20, help_text='Type of this market story', default='title',
        choices=(('title', 'Big title'), ('story', 'Story telling'), ('news', 'Simple News'))
    )
    name = models.CharField(
        default='', max_length=200, help_text='Name of the story, news, title'
    )
    desc = models.TextField(default='', blank=True, null=True)
    story = models.CharField(
        max_length=20, help_text='Current state of article telling', default='good30',
        choices=(
            ('good90', 'Good story 90% chance, 88% follow'),
            ('good30', 'Good story 30% chance, 78% follow'),
            ('bad90', 'Bad story 90% chance, 38% follow'),
            ('bad30', 'Bad story 30% chance, 7% follow')
        )
    )
    period = models.CharField(
        max_length=20, help_text='Current state of story telling', default='latest',
        choices=(
            ('latest', 'Latest 1 or 2 days'),
            ('recent', 'Recent 1 week'),
            ('forget', 'Pass 2 weeks')
        )
    )

    # news summary
    rank = models.CharField(
        max_length=20, default=None, blank=True, null=True,
        help_text='Benzinga pro news rank 14 days',
        choices=(('good', 'Good'), ('neutral', 'Neutral'), ('bad', 'Bad')),
    )
    effect = models.CharField(
        max_length=20, default='neutral', help_text='14 days price move with news',
        choices=(('bull', 'Bull'), ('neutral', 'Neutral'), ('bear', 'Bear')),
    )
    good_news = models.IntegerField(default=0, help_text='Recent good news count')
    bad_news = models.IntegerField(default=0, help_text='Recent good news count')

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
    reversed = models.BooleanField(
        default=True, help_text='Is this bad news as good news? good news as bad news?'
    )

    # news effect price probability
    bull_chance = models.FloatField(default=33, help_text='Chance of bull move by this news')
    range_chance = models.FloatField(default=34, help_text='Chance of range move by this news')
    bear_chance = models.FloatField(default=33, help_text='Chance of bear move by this news')


class StockFundamental(models.Model):
    """
    Simple fundamental analysis, micro valuation for stock, weekly update
    """
    stock_profile = models.OneToOneField(StockProfile, null=True, default=None)

    # Strong-Form Hypothesis
    # rank
    mean_rank = models.FloatField(default=3, help_text='Fundamental Mean Rank')
    accuracy = models.IntegerField(default=50, help_text='Upgrade/downgrade accuracy')
    risk = models.CharField(
        max_length=20, help_text='From S&P report', default='middle',
        choices=(('low', 'Low'), ('middle', 'Middle'), ('high', 'High'))
    )

    rank_change = models.CharField(
        max_length=20, help_text='Latest rank change', default='upgrade',
        choices=(('upgrade', 'Upgrade'), ('hold', 'Hold'), ('downgrade', 'Downgrade')),
    )
    report_date = models.DateField(
        null=True, blank=True, default=None, help_text='Latest rank change date'
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

    # report
    rt_report = models.FileField(
        upload_to=UploadRenameImage('report/stock/fundamental/rt'),
        default=None, null=True, blank=True
    )
    jaywalk_report = models.FileField(
        upload_to=UploadRenameImage('report/stock/fundamental/jaywalk'),
        default=None, null=True, blank=True
    )
    zack_report = models.FileField(
        upload_to=UploadRenameImage('report/stock/fundamental/zack'),
        default=None, null=True, blank=True
    )


class StockIndustry(models.Model):
    """
    Industry analysis, update season after earning or enter position
    """
    stock_profile = models.OneToOneField(StockProfile, null=True, default=None)

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
        max_length=20, default='middle', help_text='Zack major sector rank',
        choices=(('top', 'Top'), ('middle', 'Middle'), ('bottom', 'Bottom')),
    )

    # stock vs peer
    stock_rank = models.CharField(
        max_length=20, default='same', help_text='Zack stock rank vs peer',
        choices=(('better', 'Better'), ('same', 'Same'), ('worst', 'Worst')),
    )
    stock_growth = models.CharField(
        max_length=20, default='same', help_text='Zack stock rank vs peer',
        choices=(('better', 'Better'), ('same', 'Same'), ('worst', 'Worst')),
    )
    stock_financial = models.CharField(
        max_length=20, default='same', help_text='Zack stock rank vs peer',
        choices=(('better', 'Better'), ('same', 'Same'), ('worst', 'Worst')),
    )

    industry_report = models.FileField(
        upload_to=UploadRenameImage('report/stock/industry/pdf'),
        default=None, null=True, blank=True, help_text='Zack industry industry rank report'
    )
    compare_report = models.FileField(
        upload_to=UploadRenameImage('report/stock/industry/stock'),
        default=None, null=True, blank=True, help_text='Zack industry stock compare report'
    )


class StockOwnership(models.Model):
    """
    Current stock ownership data; history data & move in excel
    """
    stock_profile = models.OneToOneField(StockProfile, null=True, default=None)

    provide = models.BooleanField(default=True, help_text='Got ownership holding data?')
    # ownership change
    report_date = models.DateField(
        null=True, blank=True, default=None, help_text='Latest report filled date'
    )
    hold_percent = models.FloatField(default=0, help_text='How much % share institute Own? (in %)')
    outstanding = models.FloatField(default=0, help_text='How much % still in the market? (in Mil)')
    hold_value = models.DecimalField(
        default=0, max_digits=10, decimal_places=2, help_text='Total hold value (in Mil)'
    )
    pos_add = models.IntegerField(default=0, help_text='Active position increase share (in Mil)')
    pos_reduce = models.IntegerField(default=0, help_text='Active position decrease share (in Mil)')
    pos_enter = models.IntegerField(default=0, help_text='New position (in Mil)')
    pos_exit = models.IntegerField(default=0, help_text='Sold out position (in Mil)')

    pdf_report = models.FileField(
        upload_to=UploadRenameImage('report/stock/ownership/pdf'),
        default=None, null=True, blank=True
    )
    excel_report = models.FileField(
        upload_to=UploadRenameImage('report/stock/ownership/excel'),
        default=None, null=True, blank=True
    )
    desc = models.TextField(
        blank=True, null=True, default='',
        help_text='Using ownership history, careful analysis price move and explain'
    )


class StockInsider(models.Model):
    stock_profile = models.OneToOneField(StockProfile, null=True, default=None)

    provide = models.BooleanField(default=True, help_text='Got insider trading data?')
    report_date = models.DateField(
        null=True, blank=True, default=None, help_text='Latest report filled date'
    )
    report_price = models.DecimalField(
        default=0, max_digits=10, decimal_places=2, help_text='Date close price'
    )

    count_bought = models.IntegerField(default=0, help_text='3 month buy trade')
    count_sold = models.IntegerField(default=0, help_text='3 month sell trade')
    share_bought = models.IntegerField(default=0, help_text='3 month share bought')
    share_sold = models.IntegerField(default=0, help_text='3 month share sold')

    pdf_report = models.FileField(
        upload_to=UploadRenameImage('report/stock/insider/pdf'),
        default=None, null=True, blank=True
    )


class StockShortInterest(models.Model):
    stock_profile = models.OneToOneField(StockProfile, null=True, default=None)

    provide = models.BooleanField(default=True, help_text='Got short interest data?')
    report_date = models.DateField(
        null=True, blank=True, default=None, help_text='Latest short interest date'
    )
    report_price = models.DecimalField(
        default=0, max_digits=10, decimal_places=2, help_text='Date close price'
    )

    share_short = models.IntegerField(default=0, help_text='Current share shorted')
    day_cover = models.FloatField(default=0, help_text='Days To Cover')
    share_float = models.FloatField(default=0, help_text='Short float')
    share_move = models.FloatField(default=0, help_text='Short % increase/decrease')

    excel_report = models.FileField(
        upload_to=UploadRenameImage('report/stock/short_interest/excel'),
        default=None, null=True, blank=True,
        help_text='Excel data report with chart'
    )


class StockEarning(models.Model):
    stock_profile = models.OneToOneField(StockProfile, null=True, default=None)

    # earning
    prepare = models.BooleanField(default=False, help_text='Ready earning report')
    expect = models.CharField(
        max_length=20, default='uncertain', blank=True, help_text='Earning EPS expectation',
        choices=(
            ('beat', 'Beat'), ('meet', 'Meet'), ('miss', 'Miss'), ('uncertain', 'Not sure')
        ),
    )
    direction = models.CharField(
        max_length=20, default='uncertain', blank=True, help_text='Earning price movement',
        choices=(
            ('bull', 'Bull'), ('neutral', 'Neutral'), ('bear', 'Bear'), ('uncertain', 'Not sure')
        ),
    )
    move = models.FloatField(default=0, help_text='Price in % move')

    backtest = models.CharField(
        max_length=20, default='', blank=True, help_text='Earning backtest significant',
        choices=(
            ('bull', 'Bull'), ('neutral', 'Neutral'), ('bear', 'Bear'),
            ('no_test', 'No backtest')
        ),
    )
    desc = models.TextField(
        blank=True, null=True, default='',
        help_text='Using earning report & backtest result, write explaination'
    )


