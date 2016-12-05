import os
from datetime import datetime
from django.db import models
from rivers.settings import IB_STATEMENT_DIR

NAV_NAMES = {
    'Starting Value': 'nav_start',
    'Mark-to-Market': 'nav_mark',
    'Deposits & Withdrawals': 'nav_start',  # same as mark
    'Commissions': 'nav_fee',
    'Ending Value': 'nav_value',
}


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

    nav_start = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    nav_mark = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    nav_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    nav_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    unique_together = (('name', 'date'), )

    def __unicode__(self):
        return '{name} {date} {nav_value}'.format(
            name=self.name.name, date=self.date.strftime('%Y-%m-%d'), nav_value=self.nav_value
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

        ib_navs = []
        ib_marks = []
        ib_performs = []

        for line in lines:
            line = line.replace('--', '0')
            data = line.split(',')

            if len(data) == 4:
                if data[0] == 'Change in NAV' and data[1] == 'Data':
                    print NAV_NAMES[data[2]], float(data[3])
                    setattr(self, NAV_NAMES[data[2]], float(data[3]))
            elif len(data) == 8:
                if data[0] == 'Net Asset Value' and data[1] == 'Data':
                    ib_nav = IBNetAssetValue()
                    ib_nav.statement = self
                    ib_nav.asset = data[2].strip().capitalize()  # change
                    ib_nav.total0 = float(data[3])
                    ib_nav.total1 = float(data[4])
                    ib_nav.short_sum = float(data[5])
                    ib_nav.long_sum = float(data[6])
                    ib_nav.change = float(data[7])
                    ib_navs.append(ib_nav)
            elif len(data) == 14:
                if data[0] == 'Mark-to-Market Performance Summary' and data[1] == 'Data':
                    if data[2] in ('Stocks', 'Options'):
                        ib_mark = IBMarkToMarket()
                        ib_mark.statement = self
                        ib_mark.symbol = data[3]
                        ib_mark.qty0 = int(data[4])
                        ib_mark.qty1 = int(data[5])
                        ib_mark.price0 = float(data[6])
                        ib_mark.price1 = float(data[7])
                        ib_mark.pl_pos = float(data[8])
                        ib_mark.pl_trans = float(data[9])
                        ib_mark.pl_fee = float(data[10])
                        ib_mark.pl_other = float(data[11])
                        ib_mark.pl_total = float(data[12])
                        ib_marks.append(ib_mark)
            elif len(data) == 17:
                if data[0] == 'Realized & Unrealized Performance Summary' and data[1] == 'Data':
                    if data[2] in ('Stocks', 'Options'):
                        ib_perform = IBPerformance()
                        ib_perform.statement = self
                        ib_perform.symbol = data[3]
                        ib_perform.cost_adj = data[4]
                        ib_perform.real_st_profit = float(data[5])
                        ib_perform.real_st_loss = float(data[6])
                        ib_perform.real_lt_profit = float(data[7])
                        ib_perform.real_lt_loss = float(data[8])
                        ib_perform.real_total = float(data[9])
                        ib_perform.unreal_st_profit = float(data[10])
                        ib_perform.unreal_st_loss = float(data[11])
                        ib_perform.unreal_lt_profit = float(data[12])
                        ib_perform.unreal_lt_loss = float(data[13])
                        ib_perform.unreal_total = float(data[14])
                        ib_perform.total = float(data[15])
                        ib_performs.append(ib_perform)

            # IBProfitLoss

            """
            Month & Year to Date Performance Summary,Header,Asset Category,Symbol,Description,Mark-to-Market MTD,Mark-to-Market YTD,Realized S/T MTD,Realized S/T YTD,Realized L/T MTD,Realized L/T YTD
            Month & Year to Date Performance Summary,Data,Stocks,DGLD,VELOCITYSHARES 3X INVERSE GO,30.441523,30.441523,30.441523,30.441523,0,0
            Month & Year to Date Performance Summary,Data,Stocks,EWW,ISHARES MSCI MEXICO CAPPED,-176,-176,0,0,0,0
            Month & Year to Date Performance Summary,Data,Stocks,TMF,DIREXION DLY 20+Y T BULL 3X,-84.75,-84.75,0,0,0,0
            Month & Year to Date Performance Summary,Data,Stocks,UDN,POWERSHARES DB US DOL IND BE,-28.5,-28.5,0,0,0,0
            Month & Year to Date Performance Summary,Data,Stocks,UGLD,VELOCITYSHARES 3X LONG GOLD,-652.5,-652.5,0,0,0,0
            Month & Year to Date Performance Summary,Data,Total,,,-911.308477,-911.308477,30.441523,30.441523,0,0
            Month & Year to Date Performance Summary,Data,Total (All Assets),,,-911.308477,-911.308477,30.441523,30.441523,0,0
            """

            # todo: cont...

        # save ib statement
        self.save()

        if len(ib_navs):
            IBNetAssetValue.objects.bulk_create(ib_navs)

        if len(ib_marks):
            IBMarkToMarket.objects.bulk_create(ib_marks)

        if len(ib_performs):
            IBPerformance.objects.bulk_create(ib_performs)

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

