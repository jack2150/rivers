# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='IBCashReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('summary', models.CharField(max_length=50)),
                ('currency', models.CharField(default=b'Base Currency Summary', max_length=100)),
                ('total', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('security', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('future', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('pl_mtd', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('pl_ytd', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBFinancialInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('asset', models.CharField(max_length=20)),
                ('symbol', models.CharField(max_length=20)),
                ('company', models.CharField(max_length=200)),
                ('con_id', models.IntegerField(default=0)),
                ('sec_id', models.CharField(max_length=50)),
                ('multiplier', models.FloatField(default=0)),
                ('options', models.BooleanField(default=False)),
                ('ex_date', models.DateField(default=None, null=True, blank=True)),
                ('ex_month', models.DateField(default=None, null=True, blank=True)),
                ('name', models.CharField(default=None, max_length=1, null=True, blank=True)),
                ('strike', models.FloatField(default=None, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='IBInterestAccrual',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('currency', models.CharField(default=b'Base Currency Summary', max_length=100)),
                ('summary', models.CharField(max_length=50)),
                ('interest', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBMarkToMarket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('symbol', models.CharField(max_length=20)),
                ('options', models.BooleanField(default=False)),
                ('ex_date', models.DateTimeField(default=None, null=True, blank=True)),
                ('strike', models.FloatField(default=None, null=True, blank=True)),
                ('name', models.CharField(default=None, max_length=1, null=True, blank=True)),
                ('qty0', models.IntegerField(default=0)),
                ('qty1', models.IntegerField(default=0)),
                ('price0', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('price1', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('pl_pos', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('pl_trans', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('pl_fee', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('pl_other', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('pl_total', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBNetAssetValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('asset', models.CharField(max_length=20)),
                ('total', models.DecimalField(max_digits=10, decimal_places=2)),
                ('total_long', models.DecimalField(max_digits=10, decimal_places=2)),
                ('total_short', models.DecimalField(max_digits=10, decimal_places=2)),
                ('total_prior', models.DecimalField(max_digits=10, decimal_places=2)),
                ('total_change', models.DecimalField(max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBOpenPosition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('side', models.CharField(default=b'long', max_length=10)),
                ('asset', models.CharField(default=b'stocks', max_length=50)),
                ('currency', models.CharField(default=b'USD', max_length=20)),
                ('symbol', models.CharField(max_length=20)),
                ('options', models.BooleanField(default=False)),
                ('ex_date', models.DateTimeField(default=None, null=True, blank=True)),
                ('strike', models.FloatField(default=None, null=True, blank=True)),
                ('name', models.CharField(default=None, max_length=1, null=True, blank=True)),
                ('qty', models.IntegerField(default=0)),
                ('multiplier', models.FloatField(default=0)),
                ('cost_price', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('cost_basic', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('close_price', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('total_value', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('unreal_pl', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('nav_pct', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBPerformance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('symbol', models.CharField(max_length=20)),
                ('options', models.BooleanField(default=False)),
                ('ex_date', models.DateTimeField(default=None, null=True, blank=True)),
                ('strike', models.FloatField(default=None, null=True, blank=True)),
                ('name', models.CharField(default=None, max_length=1, null=True, blank=True)),
                ('cost_adj', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('real_st_profit', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('real_st_loss', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('real_lt_profit', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('real_lt_loss', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('real_total', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('unreal_st_profit', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('unreal_st_loss', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('unreal_lt_profit', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('unreal_lt_loss', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('unreal_total', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('total', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBPosition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('symbol', models.CharField(default=b'', max_length=20)),
                ('date0', models.DateField(default=None)),
                ('date1', models.DateField(default=None, null=True, blank=True)),
                ('status', models.CharField(default=b'open', max_length=50, choices=[(b'open', b'Open'), (b'close', b'Close'), (b'expire', b'Expire')])),
            ],
        ),
        migrations.CreateModel(
            name='IBPositionTrade',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.CharField(default=b'trade', max_length=20)),
                ('asset', models.CharField(max_length=20)),
                ('currency', models.CharField(default=b'USD', max_length=20)),
                ('symbol', models.CharField(max_length=20)),
                ('options', models.BooleanField(default=False)),
                ('ex_date', models.DateTimeField(default=None, null=True, blank=True)),
                ('strike', models.FloatField(default=None, null=True, blank=True)),
                ('name', models.CharField(default=None, max_length=1, null=True, blank=True)),
                ('date_time', models.DateTimeField()),
                ('exchange', models.CharField(default=b'AUTO', max_length=100, blank=True)),
                ('qty', models.IntegerField(default=0)),
                ('trade_price', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('cost_price', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('proceed', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('fee', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('real_pl', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('mtm_pl', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('position', models.ForeignKey(default=None, blank=True, to='ib.IBPosition', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='IBProfitLoss',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('asset', models.CharField(max_length=20)),
                ('symbol', models.CharField(max_length=20)),
                ('options', models.BooleanField(default=False)),
                ('option_code', models.CharField(default=None, max_length=100, null=True, blank=True)),
                ('company', models.CharField(default=None, max_length=200, null=True, blank=True)),
                ('ex_date', models.DateTimeField(default=None, null=True, blank=True)),
                ('strike', models.FloatField(default=None, null=True, blank=True)),
                ('name', models.CharField(default=None, max_length=1, null=True, blank=True)),
                ('pl_mtd', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('pl_ytd', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('real_st_mtd', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('real_st_ytd', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('real_lt_mtd', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('real_lt_ytd', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('position', models.ForeignKey(default=None, blank=True, to='ib.IBPosition', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='IBStatement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('stock_prior', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('stock_trans', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('stock_pl_mtm_prior', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('stock_pl_mtm_trans', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('stock_end', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('option_prior', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('option_trans', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('option_pl_mtm_prior', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('option_pl_mtm_trans', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
                ('option_end', models.DecimalField(default=0, max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBStatementName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('real_name', models.CharField(max_length=100)),
                ('broker', models.CharField(default=b'Interactive brokers', max_length=100)),
                ('account_id', models.CharField(max_length=50)),
                ('account_type', models.CharField(default=b'Individual', max_length=200)),
                ('customer_type', models.CharField(default=b'Individual', max_length=200)),
                ('capability', models.CharField(default=b'Margin', max_length=200)),
                ('path', models.CharField(max_length=100)),
                ('start', models.DateField()),
                ('stop', models.DateField(null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='ibstatement',
            name='statement_name',
            field=models.ForeignKey(to='ib.IBStatementName'),
        ),
        migrations.AddField(
            model_name='ibprofitloss',
            name='statement',
            field=models.ForeignKey(to='ib.IBStatement'),
        ),
        migrations.AddField(
            model_name='ibpositiontrade',
            name='statement',
            field=models.ForeignKey(to='ib.IBStatement'),
        ),
        migrations.AddField(
            model_name='ibposition',
            name='statement_name',
            field=models.ForeignKey(to='ib.IBStatementName'),
        ),
        migrations.AddField(
            model_name='ibperformance',
            name='position',
            field=models.ForeignKey(default=None, blank=True, to='ib.IBPosition', null=True),
        ),
        migrations.AddField(
            model_name='ibperformance',
            name='statement',
            field=models.ForeignKey(to='ib.IBStatement'),
        ),
        migrations.AddField(
            model_name='ibopenposition',
            name='position',
            field=models.ForeignKey(default=None, blank=True, to='ib.IBPosition', null=True),
        ),
        migrations.AddField(
            model_name='ibopenposition',
            name='statement',
            field=models.ForeignKey(to='ib.IBStatement'),
        ),
        migrations.AddField(
            model_name='ibnetassetvalue',
            name='statement',
            field=models.ForeignKey(to='ib.IBStatement'),
        ),
        migrations.AddField(
            model_name='ibmarktomarket',
            name='position',
            field=models.ForeignKey(default=None, blank=True, to='ib.IBPosition', null=True),
        ),
        migrations.AddField(
            model_name='ibmarktomarket',
            name='statement',
            field=models.ForeignKey(to='ib.IBStatement'),
        ),
        migrations.AddField(
            model_name='ibinterestaccrual',
            name='statement',
            field=models.ForeignKey(to='ib.IBStatement'),
        ),
        migrations.AddField(
            model_name='ibfinancialinfo',
            name='position',
            field=models.ForeignKey(default=None, blank=True, to='ib.IBPosition', null=True),
        ),
        migrations.AddField(
            model_name='ibfinancialinfo',
            name='statement',
            field=models.ForeignKey(to='ib.IBStatement'),
        ),
        migrations.AddField(
            model_name='ibcashreport',
            name='statement',
            field=models.ForeignKey(to='ib.IBStatement'),
        ),
    ]
