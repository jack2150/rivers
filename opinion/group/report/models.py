import datetime
from django.db import models


class ReportEnter(models.Model):
    """
    A stock report contain of
    fundamental, industry, tech rank, tech opinion,
    market news, trade idea, enter opinion, and etc
    """
    symbol = models.CharField(max_length=10)
    date = models.DateField(default=datetime.datetime.now)
    unique_together = (('symbol', 'date'),)

    close = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __unicode__(self):
        return 'ReportEnter <{symbol}> {date}'.format(
            symbol=self.symbol, date=self.date
        )

    # todo: backtest


class SubtoolOpinion(models.Model):
    """
    Use for summarize sub tool result
    """
    report_enter = models.ForeignKey(ReportEnter, null=True, blank=True)

    name = models.CharField(
        choices=(
            ('excel', 'Excel'), ('op_timesale', 'Options timesale'), ('minute1', 'Minute1')
        ),  # more will be add later
        max_length=20, help_text='Subtool name', default='excel'
    )
    hour = models.IntegerField(default=12)
    unique_together = (('name', 'hour'),)  # every hour only 1 report
    direction = models.CharField(
        choices=(('bull', 'Bull'), ('range', 'Range'), ('bear', 'Bear')),
        max_length=20, help_text='Estimate result direction', default='range'
    )











