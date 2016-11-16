# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='IBCashReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=20)),
                ('currency', models.CharField(default=b'Base Currency Summary', max_length=20)),
                ('total', models.DecimalField(max_digits=10, decimal_places=2)),
                ('security', models.DecimalField(max_digits=10, decimal_places=2)),
                ('future', models.DecimalField(max_digits=10, decimal_places=2)),
                ('pl_mtd', models.DecimalField(max_digits=10, decimal_places=2)),
                ('pl_ytd', models.DecimalField(max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBFinancialInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('asset', models.CharField(max_length=20)),
                ('symbol', models.CharField(max_length=20)),
                ('company', models.CharField(max_length=200)),
                ('con_id', models.IntegerField()),
                ('sec_id', models.IntegerField()),
                ('multiplier', models.FloatField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='IBMarkToMarket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('symbol', models.CharField(max_length=20)),
                ('qty0', models.IntegerField()),
                ('qty1', models.IntegerField()),
                ('price0', models.DecimalField(max_digits=10, decimal_places=2)),
                ('price1', models.DecimalField(max_digits=10, decimal_places=2)),
                ('pl_pos', models.DecimalField(max_digits=10, decimal_places=2)),
                ('pl_trans', models.DecimalField(max_digits=10, decimal_places=2)),
                ('pl_fee', models.DecimalField(max_digits=10, decimal_places=2)),
                ('pl_other', models.DecimalField(max_digits=10, decimal_places=2)),
                ('pl_total', models.DecimalField(max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBNetAssetValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('asset', models.CharField(max_length=20)),
                ('total0', models.DecimalField(max_digits=10, decimal_places=2)),
                ('total1', models.DecimalField(max_digits=10, decimal_places=2)),
                ('short_sum', models.DecimalField(max_digits=10, decimal_places=2)),
                ('long_sum', models.DecimalField(max_digits=10, decimal_places=2)),
                ('change', models.DecimalField(max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBOpenPosition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('asset', models.CharField(max_length=20)),
                ('currency', models.CharField(default=b'USD', max_length=20)),
                ('symbol', models.CharField(max_length=20)),
                ('date_time', models.DateTimeField()),
                ('qty', models.IntegerField(default=0)),
                ('multiplier', models.FloatField(default=0)),
                ('cost_price', models.DecimalField(max_digits=10, decimal_places=2)),
                ('cost_basic', models.DecimalField(max_digits=10, decimal_places=2)),
                ('close_price', models.DecimalField(max_digits=10, decimal_places=2)),
                ('total_value', models.DecimalField(max_digits=10, decimal_places=2)),
                ('unreal_pl', models.DecimalField(max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBPerformance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('symbol', models.CharField(max_length=20)),
                ('cost_adj', models.DecimalField(max_digits=10, decimal_places=2)),
                ('real_st_profit', models.DecimalField(max_digits=10, decimal_places=2)),
                ('real_st_loss', models.DecimalField(max_digits=10, decimal_places=2)),
                ('real_lt_profit', models.DecimalField(max_digits=10, decimal_places=2)),
                ('real_lt_loss', models.DecimalField(max_digits=10, decimal_places=2)),
                ('real_total', models.DecimalField(max_digits=10, decimal_places=2)),
                ('unreal_st_profit', models.DecimalField(max_digits=10, decimal_places=2)),
                ('unreal_st_loss', models.DecimalField(max_digits=10, decimal_places=2)),
                ('unreal_lt_profit', models.DecimalField(max_digits=10, decimal_places=2)),
                ('unreal_lt_loss', models.DecimalField(max_digits=10, decimal_places=2)),
                ('unreal_total', models.DecimalField(max_digits=10, decimal_places=2)),
                ('total', models.DecimalField(max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBPositionTrade',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('asset', models.CharField(max_length=20)),
                ('currency', models.CharField(default=b'USD', max_length=20)),
                ('symbol', models.CharField(max_length=20)),
                ('date_time', models.DateTimeField()),
                ('exchange', models.CharField(max_length=100)),
                ('qty', models.IntegerField(default=0)),
                ('trade_price', models.DecimalField(max_digits=10, decimal_places=2)),
                ('close_price', models.DecimalField(max_digits=10, decimal_places=2)),
                ('proceed', models.DecimalField(max_digits=10, decimal_places=2)),
                ('fee', models.DecimalField(max_digits=10, decimal_places=2)),
                ('real_pl', models.DecimalField(max_digits=10, decimal_places=2)),
                ('mtm_pl', models.DecimalField(max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBProfitLoss',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('asset', models.CharField(max_length=20)),
                ('symbol', models.CharField(max_length=20)),
                ('company', models.CharField(max_length=200)),
                ('pl_mtd', models.DecimalField(max_digits=10, decimal_places=2)),
                ('pl_ytd', models.DecimalField(max_digits=10, decimal_places=2)),
                ('real_st_mtd', models.DecimalField(max_digits=10, decimal_places=2)),
                ('real_st_ytd', models.DecimalField(max_digits=10, decimal_places=2)),
                ('real_lt_mtd', models.DecimalField(max_digits=10, decimal_places=2)),
                ('real_lt_ytd', models.DecimalField(max_digits=10, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='IBStatement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='IBStatementName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('broker_id', models.CharField(max_length=50)),
                ('account_type', models.CharField(default=b'Individual', max_length=200)),
                ('customer_type', models.CharField(default=b'Individual', max_length=200)),
                ('capability', models.CharField(default=b'Margin', max_length=200)),
                ('path', models.CharField(max_length=100)),
                ('start_date', models.DateField()),
                ('stop_date', models.DateField(null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='ibstatement',
            name='name',
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
            model_name='ibperformance',
            name='statement',
            field=models.ForeignKey(to='ib.IBStatement'),
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
            name='statement',
            field=models.ForeignKey(to='ib.IBStatement'),
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
