from django.db import models
from django.db.models import Q


class OptionTimeSale(models.Model):
    symbol = models.CharField(max_length=20)
    date = models.DateField()

    unique_together = (('symbol', 'date'),)

