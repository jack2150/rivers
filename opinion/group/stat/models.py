from django.db import models
from opinion.group.report.models import UnderlyingReport


class StatPrice(models.Model):
    symbol = models.CharField(max_length=20)
    date = models.DateField()

    move = models.FloatField(default=0, help_text='Current move')
    rare = models.CharField(
        choices=(
            ('normal', 'Normal - within 1 std'),
            ('rare', 'Rare - between 1 std'),
            ('very_rare', 'Very rare - above 1 std')
        ),
        max_length=50, default='normal', help_text='Rarely of price movement'
    )

    bday5d = models.FloatField(default=0, help_text='Hold 5 bdays return')
    bday20d = models.FloatField(default=0, help_text='Hold 20 bdays return')
    bday60d = models.FloatField(default=0, help_text='Hold 60 bdays return')

    opportunity = models.BooleanField(default=False, help_text='Is this a opportunity to enter?')
