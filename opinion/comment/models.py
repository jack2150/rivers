from django.db import models


class PortfolioOpinion(models.Model):
    date = models.DateField()

    trades = models.IntegerField(default=0, help_text='How many trade you made today?')
    pl_ytd = models.FloatField(default=0, help_text='Profit/Loss year to date!')
    performance = models.CharField(
        max_length=50, default='normal', choices=(
            ('best', 'Best'), ('good', 'Good'), ('normal', 'Normal'),
            ('bad', 'Bad'), ('trouble', 'Trouble')
        )
    )

    emotion = models.TextField(
        default='', blank=True, null=True, help_text='How you feel for trading today?'
    )
    position = models.TextField(
        default='', blank=True, null=True, help_text='Quick note for every single positions?'
    )
    movement = models.TextField(
        default='', blank=True, null=True, help_text='Portfolio movement for today, good or bad?'
    )
    expectation = models.TextField(
        default='', blank=True, null=True, help_text='What you expectation for this portfolio tomorrow?'
    )
    research = models.TextField(
        default='', blank=True, null=True, help_text='What you watch/research today?'
    )


class WeekdayOpinion(models.Model):
    """
    Basic stock movement and news/information, daily update
    """
    symbol = models.CharField(max_length=6)
    date = models.DateField()

    # unique data
    unique_together = (('symbol', 'date'),)

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

    # unique data
    unique_together = (('symbol', 'date'),)

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
            ('both', 'Earning & Dividend'),
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

    # unique data
    unique_together = (('symbol', 'date'),)

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

