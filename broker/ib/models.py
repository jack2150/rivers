import os
from datetime import datetime
from django.db import models
from rivers.settings import IB_STATEMENT_DIR


class IBStatementName(models.Model):
    name = models.CharField(max_length=100)
    broker_id = models.CharField(max_length=50)
    account_type = models.CharField(max_length=200, default='Individual')
    customer_type = models.CharField(max_length=200, default='Individual')
    capability = models.CharField(max_length=200, default='Margin')
    path = models.CharField(max_length=100)
    start = models.DateField()
    stop = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return '{name}'.format(
            name=self.name
        )


class IBStatement(models.Model):
    name = models.ForeignKey(IBStatementName)
    date = models.DateField()

    unique_together = (('name', 'date'), )

    def __unicode__(self):
        return '{name} {date}'.format(
            name=self.name.name, date=self.date.strftime('%Y-%m-%d')
        )

    def statement_import(self, statement_name, fname):
        """
        Open a ib daily statement file
        then extract data from file and
        save into db
        :param statement_name: IBStatementName
        :param fname: str
        :return: IBStatement
        """
        path = os.path.join(IB_STATEMENT_DIR, statement_name.path, fname)
        date = os.path.basename(path).split('_')[-1].split('.')[0]

        if not self.id:
            self.name = statement_name
            self.date = datetime.strptime(date, '%Y%m%d')
            self.save()

        if self.ibnetassetvalue_set.count() > 0:  # done
            return self

        lines = open(path).readlines()

        ib_statements = []
        for line in lines:
            data = line.split(',')

            found = False
            if len(data) == 8:
                if data[0] == 'Net Asset Value' and data[1] == 'Data':
                    found = True

            if found:
                ib_statement = IBNetAssetValue()
                ib_statement.statement = self
                ib_statement.asset = data[2].strip().capitalize() # change
                ib_statement.total0 = float(data[3])
                ib_statement.total1 = float(data[4])
                ib_statement.short_sum = float(data[5])
                ib_statement.long_sum = float(data[6])
                ib_statement.change = float(data[7])
                ib_statements.append(ib_statement)

        if len(ib_statements):
            IBNetAssetValue.objects.bulk_create(ib_statements)

        return self


class IBNetAssetValue(models.Model):
    statement = models.ForeignKey(IBStatement)

    asset = models.CharField(max_length=20)
    total0 = models.DecimalField(max_digits=10, decimal_places=2)
    total1 = models.DecimalField(max_digits=10, decimal_places=2)
    short_sum = models.DecimalField(max_digits=10, decimal_places=2)
    long_sum = models.DecimalField(max_digits=10, decimal_places=2)
    change = models.DecimalField(max_digits=10, decimal_places=2)

    def __unicode__(self):
        """
        Output data
        :return: str
        """
        return '{asset} {total0} {total1} {short_sum} {long_sum} {change}'.format(
            asset=self.asset,
            total0=self.total0,
            total1=self.total1,
            short_sum=self.short_sum,
            long_sum=self.long_sum,
            change=self.change
        )


class IBMarkToMarket(models.Model):
    statement = models.ForeignKey(IBStatement)

    symbol = models.CharField(max_length=20)
    qty0 = models.IntegerField()
    qty1 = models.IntegerField()
    price0 = models.DecimalField(max_digits=10, decimal_places=2)
    price1 = models.DecimalField(max_digits=10, decimal_places=2)

    pl_pos = models.DecimalField(max_digits=10, decimal_places=2)
    pl_trans = models.DecimalField(max_digits=10, decimal_places=2)
    pl_fee = models.DecimalField(max_digits=10, decimal_places=2)
    pl_other = models.DecimalField(max_digits=10, decimal_places=2)
    pl_total = models.DecimalField(max_digits=10, decimal_places=2)


class IBPerformance(models.Model):
    statement = models.ForeignKey(IBStatement)

    symbol = models.CharField(max_length=20)
    cost_adj = models.DecimalField(max_digits=10, decimal_places=2)
    real_st_profit = models.DecimalField(max_digits=10, decimal_places=2)  # short term
    real_st_loss = models.DecimalField(max_digits=10, decimal_places=2)
    real_lt_profit = models.DecimalField(max_digits=10, decimal_places=2)  # long term
    real_lt_loss = models.DecimalField(max_digits=10, decimal_places=2)
    real_total = models.DecimalField(max_digits=10, decimal_places=2)

    unreal_st_profit = models.DecimalField(max_digits=10, decimal_places=2)  # short term
    unreal_st_loss = models.DecimalField(max_digits=10, decimal_places=2)
    unreal_lt_profit = models.DecimalField(max_digits=10, decimal_places=2)  # long term
    unreal_lt_loss = models.DecimalField(max_digits=10, decimal_places=2)
    unreal_total = models.DecimalField(max_digits=10, decimal_places=2)

    total = models.DecimalField(max_digits=10, decimal_places=2)


class IBProfitLoss(models.Model):
    statement = models.ForeignKey(IBStatement)

    asset = models.CharField(max_length=20)
    symbol = models.CharField(max_length=20)
    company = models.CharField(max_length=200)
    pl_mtd = models.DecimalField(max_digits=10, decimal_places=2)
    pl_ytd = models.DecimalField(max_digits=10, decimal_places=2)
    real_st_mtd = models.DecimalField(max_digits=10, decimal_places=2)  # short term
    real_st_ytd = models.DecimalField(max_digits=10, decimal_places=2)
    real_lt_mtd = models.DecimalField(max_digits=10, decimal_places=2)  # long term
    real_lt_ytd = models.DecimalField(max_digits=10, decimal_places=2)


class IBCashReport(models.Model):
    statement = models.ForeignKey(IBStatement)

    name = models.CharField(max_length=20)

    currency = models.CharField(max_length=20, default='Base Currency Summary')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    security = models.DecimalField(max_digits=10, decimal_places=2)
    future = models.DecimalField(max_digits=10, decimal_places=2)
    pl_mtd = models.DecimalField(max_digits=10, decimal_places=2)
    pl_ytd = models.DecimalField(max_digits=10, decimal_places=2)


class IBOpenPosition(models.Model):
    statement = models.ForeignKey(IBStatement)

    asset = models.CharField(max_length=20)
    currency = models.CharField(max_length=20, default='USD')
    symbol = models.CharField(max_length=20)
    date_time = models.DateTimeField()
    qty = models.IntegerField(default=0)
    multiplier = models.FloatField(default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_basic = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_value = models.DecimalField(max_digits=10, decimal_places=2)
    unreal_pl = models.DecimalField(max_digits=10, decimal_places=2)


class IBPositionTrade(models.Model):
    statement = models.ForeignKey(IBStatement)

    asset = models.CharField(max_length=20)
    currency = models.CharField(max_length=20, default='USD')
    symbol = models.CharField(max_length=20)
    date_time = models.DateTimeField()
    exchange = models.CharField(max_length=100)
    qty = models.IntegerField(default=0)
    trade_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    proceed = models.DecimalField(max_digits=10, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    real_pl = models.DecimalField(max_digits=10, decimal_places=2)
    mtm_pl = models.DecimalField(max_digits=10, decimal_places=2)


class IBFinancialInfo(models.Model):
    statement = models.ForeignKey(IBStatement)

    asset = models.CharField(max_length=20)
    symbol = models.CharField(max_length=20)
    company = models.CharField(max_length=200)
    con_id = models.IntegerField()
    sec_id = models.IntegerField()
    multiplier = models.FloatField(default=0)

