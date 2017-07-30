from django.db import models


class QuestLine(models.Model):
    name = models.CharField(max_length=100)
    start = models.DateField()
    stop = models.DateField(blank=True, null=True)
    active = models.BooleanField(default=False)

    # objective
    goal = models.CharField(
        choices=(('make_money', 'Make money'), ('test_portfolio', 'Test portfolio'),
                 ('income', 'Income'), ('others', 'Others')),
        max_length=50, help_text='Goal of this trading plan'
    )

    # target, stop if portfolio hit target or drawdown
    profit_target = models.FloatField(
        default=10, help_text='Portfolio max target profit'
    )
    loss_drawdown = models.FloatField(
        default=10, help_text='Portfolio max loss drawdown'
    )

    # position
    pos_size0 = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        help_text='Low risk position size'
    )
    pos_size1 = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        help_text='Middle risk position size'
    )
    pos_size2 = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        help_text='High risk position size'
    )
    holding_num = models.IntegerField(
        default=0, help_text='Average holding position number'
    )

    # risk
    risk_profile = models.CharField(
        max_length=20,
        choices=(('low', 'Low'), ('normal', 'Normal'), ('high', 'High')),
        help_text='Risk profile for this trading plan'
    )
    max_loss = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    max_profit = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    # time period
    holding_period = models.CharField(
        max_length=20,
        choices=(('short', 'Short'), ('middle', 'Middle'), ('long', 'Long')),
        help_text='Holding period for all positions'
    )
    by_term = models.CharField(
        max_length=20, default='month',
        choices=(('days', 'Days'), ('week', 'Week'), ('month', 'Month'), ('year', 'Year')),
        help_text='Holding period for all positions'
    )
    term_value = models.IntegerField(default=1, help_text='Value for holding term')

    # instrument
    instrument = models.CharField(
        max_length=20,
        choices=(('stock', 'Stock/ETF only'), ('option', 'Options only'), ('all', 'Stock & Options')),
        help_text='Instrument that use for this plan'
    )
    custom_item = models.CharField(
        max_length=50, blank=True, null=True, default='',
        help_text='Extra note on instrument used'
    )
    symbols = models.TextField(
        default='', null=True, blank=True, help_text='Common symbol used for this trading plane'
    )

    # trade
    trade_enter = models.CharField(
        max_length=20,
        choices=(('daily', 'Daily'), ('timing', 'Timing'), ('prepare', 'Prepare'), ('others', 'Others')),
        help_text='How often you enter trade'
    )
    trade_exit = models.CharField(
        max_length=20,
        choices=(('daily', 'Daily'), ('expire', 'Expire'), ('profit', 'Profit')),
        help_text='How often you exit trade'
    )
    trade_adjust = models.CharField(
        max_length=20,
        choices=(('require', 'Require'), ('timing', 'Timing'), ('confidence', 'Confidence')),
        help_text='How often you adjust position'
    )

    # note
    description = models.TextField(
        default='', null=True, blank=True, help_text='Explain trading plan here'
    )

    # result
    plan_result = models.CharField(
        choices=(('none', 'None'), ('huge_loss', 'Huge loss'), ('loss', 'Loss'), ('even', 'Even'),
                 ('profit', 'Profit'), ('huge_profit', 'Huge Profit')),
        max_length=20, help_text='Result of this plan'
    )
    plan_return = models.FloatField(
        default=0, help_text='Return of this trading plan'
    )
    advantage = models.TextField(
        blank=True, null=True, default='', help_text='Advantage of this trading plane'
    )
    weakness = models.TextField(
        blank=True, null=True, default='', help_text='Weakness of this trading plane'
    )
    conclusion = models.TextField(
        blank=True, null=True, default='', help_text='Trading plan conclusion'
    )

    def __unicode__(self):
        return '{name}'.format(name=self.name)


class QuestPart(models.Model):
    """
    Trading quest is smaller goal of trading plan
    a trading plan combine some quest to complete
    for example:
    trading plan 10% portfolio return
    trading quest 3% portfolio return
    trading quest no make mistake 1 week
    trading quest real forecast next 30 days
    trading quest hold 3 positions 10 more days
    trading quest capture more profit tick
    """
    trading_plan = models.ForeignKey(QuestLine, limit_choices_to={'active': True})

    # quest
    name = models.CharField(max_length=100)
    category = models.CharField(
        choices=(('management', 'Management'), ('portfolio', 'Portfolio'),
                 ('behavior', 'Behavior'), ('compromise', 'Compromise'),
                 ('avoid', 'Avoid'), ('analysis', 'Analysis')),
        max_length=50,
    )
    start = models.DateField()
    stop = models.DateField(blank=True, null=True)
    desc = models.TextField(null=True, blank=True, default='', max_length=300)

    # result
    progress = models.CharField(
        choices=(('complete', 'Complete'), ('partial', 'Partial'), ('fail', 'Fail'),
                 ('abandon', 'Abandon')),
        max_length=50, blank=True, null=True, default='partial'
    )
    result = models.CharField(
        choices=(('good', 'Good'), ('normal', 'Normal'), ('bad', 'Bad'),
                 ('unknown', 'Unknown')),
        max_length=50, blank=True, null=True, default='unknown'
    )
    context = models.TextField(null=True, blank=True, default='', max_length=300)

    def __unicode__(self):
        return '{name} ({stop})'.format(name=self.name, stop=self.stop)
