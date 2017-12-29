import datetime
from django.db import models


class UnderlyingReport(models.Model):
    """
    A stock report contain of
    fundamental, industry, tech rank, tech opinion,
    market news, trade idea, enter opinion, and etc
    """
    symbol = models.CharField(max_length=10)
    date = models.DateField(default=datetime.datetime.now)
    asset = models.CharField(
        choices=(('stock', 'Stock'), ('etf', 'ETF')),
        max_length=20, default='stock'
    )
    phase = models.CharField(
        choices=(('enter', 'Enter'), ('hold', 'Hold'), ('exit', 'Exit')),
        max_length=20, default='enter'
    )
    unique_together = (('symbol', 'date', 'group'),)

    close = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __unicode__(self):
        return 'Report{group} <{symbol}> {date}'.format(
            group=self.phase.capitalize(), symbol=self.symbol, date=self.date
        )


# todo: report for hold into mutli model, exit
