from datetime import datetime
from django.db import models


class SkewButterflySet(models.Model):
    name = models.CharField(max_length=100)

    create_date = models.DateField(default=datetime.now)
    expire_date = models.DateField(unique=True)

    capital = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    risk = models.DecimalField(default=0, max_digits=10, decimal_places=2)


class SkewButterfly(models.Model):
    portfolio = models.ForeignKey(SkewButterflySet)

    symbol = models.CharField(max_length=20)
    close = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    skew = models.CharField(
        max_length=50, choices=(('long', 'Long'), ('short', 'Short')), default='long'
    )

    qty = models.IntegerField(default=0)
    dte = models.IntegerField(default=0)
    enter_date = models.DateField(default=datetime.now)
    enter_price = models.DecimalField(default=0, max_digits=10, decimal_places=2)

    # options
    strike0 = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    price0 = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    multi0 = models.IntegerField(default=0)

    strike1 = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    price1 = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    multi1 = models.IntegerField(default=0)

    strike2 = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    price2 = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    multi2 = models.IntegerField(default=0)



