"""
Statement analysis is use for
better understanding your trade
and how you manage portfolio over time
Using visual data & morningstar x-ray tools
"""

# commentary
from django.db import models
from base.ufunc import UploadRenameImage, UploadDataHeroImage


class IBMonthStatement(models.Model):
    date = models.DateField(help_text='Monthly')

    def __unicode__(self):
        return 'IBMonthStatement {date}'.format(date=self.date)


class IBMonthNav(models.Model):
    """
    From NAV to cash report flow, weekly
    Using chart with csv data export
    """
    ib_month = models.OneToOneField(IBMonthStatement)

    # return
    return_month = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Return without fee'
    )
    return_real = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Return after fee'
    )
    return_taxed = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Return after fee/taxed <10%'
    )
    return_comment = models.TextField(
        blank=True, default='What to do better improve return?\n', null=True,
        help_text='NAV total return comment'
    )
    return_chart0 = models.FileField(
        blank=True, null=True, default=None, help_text='Month Return',
        upload_to=UploadDataHeroImage('statement/ib/nav/return0')
    )
    return_chart1 = models.FileField(
        blank=True, null=True, default=None, help_text='Weekly Return',
        upload_to=UploadDataHeroImage('statement/ib/nav/return1')
    )
    return_chart2 = models.FileField(
        blank=True, null=True, default=None, help_text='Daily Return',
        upload_to=UploadDataHeroImage('statement/ib/nav/return2')
    )

    # daily movement
    change_max = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Max change in month'
    )
    change_min = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Min change in month'
    )
    change_mean = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Mean change in month'
    )
    change_review = models.CharField(
        max_length=50, help_text='', default='',
        choices=(
            ('unstable', 'Unstable - account change is unstable, sometime spike'),
            ('stable', 'Stable - account change is stable, stay within range'),
        )
    )
    change_comment = models.TextField(
        blank=True, default='What to do lower risk & higher return daily?\n',
        null=True, help_text='Daily risk/return comment'
    )
    change_chart = models.FileField(
        blank=True, null=True, default=None, help_text='Change',
        upload_to=UploadDataHeroImage('statement/ib/nav/change')
    )

    # asset, cash, long/short
    cash_reserve = models.CharField(
        max_length=50, help_text='How much cash reserve in account?', default='small',
        choices=(
            ('large', 'Large - a lot of cash stay in account without trade'),
            ('medium', 'Medium - around 50% of cash in account waiting to trade'),
            ('small', 'Small - only a little bit of cash is remain in account'),
            ('fixed', 'Fixed - certain amount of cash is reserve in account'),
        )
    )
    asset_balance = models.CharField(
        max_length=50, help_text='Account balance use for stock or options', default='balance',
        choices=(
            ('balance', 'Balance - stock/options is balance'),
            ('small_gap', 'Small gap - small gap between invest in stock/options'),
            ('large_gap', 'Large gap - too much in stock/options that others'),
            ('unbalance', 'Unbalance - stock/options not balance at all'),
        )
    )
    long_short = models.CharField(
        max_length=50, help_text='Long or short for holding positions?', default='balance',
        choices=(
            ('long', 'Long - holding more long than short positions'),
            ('balance', 'Balance - long and short positions are balance'),
            ('short', 'Short holding more short than long positions'),
        )
    )
    asset_comment = models.TextField(
        blank=True, default='What target for next month reserve cash?\n\n'
                            'What target for next month stock/options asset?\n\n'
                            'What target for next month long/short positions?\n\n',
        null=True, help_text='All assets comment'
    )
    asset_chart0 = models.FileField(
        blank=True, null=True, default=None, help_text='Cash',
        upload_to=UploadDataHeroImage('statement/ib/nav/asset0')
    )
    asset_chart1 = models.FileField(
        blank=True, null=True, default=None, help_text='Cash',
        upload_to=UploadDataHeroImage('statement/ib/nav/asset1')
    )
    asset_chart2 = models.FileField(
        blank=True, null=True, default=None, help_text='Cash',
        upload_to=UploadDataHeroImage('statement/ib/nav/asset2')
    )
    asset_chart3 = models.FileField(
        blank=True, null=True, default=None, help_text='Asset',
        upload_to=UploadDataHeroImage('statement/ib/nav/asset3')
    )
    asset_chart4 = models.FileField(
        blank=True, null=True, default=None, help_text='Long/Short',
        upload_to=UploadDataHeroImage('statement/ib/nav/asset4')
    )
    asset_chart5 = models.FileField(
        blank=True, null=True, default=None, help_text='Long/Short',
        upload_to=UploadDataHeroImage('statement/ib/nav/asset5')
    )
    asset_chart6 = models.FileField(
        blank=True, null=True, default=None, help_text='Long/Short',
        upload_to=UploadDataHeroImage('statement/ib/nav/asset6')
    )

    def __unicode__(self):
        return '{return_month}'.format(
            return_month=self.return_month
        )


class IBMonthMark(models.Model):
    """
    For holding position or mark to market
    underlying what you hold, why you hold over time
    """
    ib_month = models.OneToOneField(IBMonthStatement)

    pl_stock = models.CharField(
        max_length=50, help_text='Hold profit or loss stock position?', default='even',
        choices=(
            ('profit', 'Profit - most holding stock positions is profit'),
            ('even', 'Even - holding stock position mostly even'),
            ('loss', 'Loss - most holding stock positions is loss'),
        )
    )
    pl_option = models.CharField(
        max_length=50, help_text='Hold profit or loss option position?', default='even',
        choices=(
            ('profit', 'Profit - most holding options positions is profit'),
            ('even', 'Even - holding options positions mostly even'),
            ('loss', 'Loss - most holding options positions is loss'),
        )
    )
    asset = models.CharField(
        max_length=50, help_text='Hold stock or options position?', default='balance',
        choices=(
            ('stock', 'Stock - most hold position are stocks'),
            ('balance', 'Balance - half stock positions and half options positions'),
            ('option', 'Option - most hold position are options'),
        )
    )
    change_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Month hold change'
    )
    change_move = models.CharField(
        max_length=50, help_text='Monthly change on your holding?', default='even',
        choices=(
            ('profit', 'Profit - month weekly move are mostly in profit'),
            ('even', 'Even - month weekly move are mostly even'),
            ('loss', 'Loss - month weekly move are mostly in loss'),
        )
    )

    pl_chart0 = models.FileField(
        blank=True, null=True, default=None, help_text='Profit/Loss',
        upload_to=UploadDataHeroImage('statement/ib/mark/pl0')
    )
    pl_chart1 = models.FileField(
        blank=True, null=True, default=None, help_text='Profit/Loss',
        upload_to=UploadDataHeroImage('statement/ib/mark/pl1')
    )
    pl_chart2 = models.FileField(
        blank=True, null=True, default=None, help_text='Profit/Loss',
        upload_to=UploadDataHeroImage('statement/ib/mark/pl2')
    )
    pl_chart3 = models.FileField(
        blank=True, null=True, default=None, help_text='Profit/Loss',
        upload_to=UploadDataHeroImage('statement/ib/mark/pl3')
    )
    pl_chart4 = models.FileField(
        blank=True, null=True, default=None, help_text='Profit/Loss',
        upload_to=UploadDataHeroImage('statement/ib/mark/pl4')
    )
    pl_chart5 = models.FileField(
        blank=True, null=True, default=None, help_text='Profit/Loss',
        upload_to=UploadDataHeroImage('statement/ib/mark/pl5')
    )
    change_chart = models.FileField(
        blank=True, null=True, default=None, help_text='Change',
        upload_to=UploadDataHeroImage('statement/ib/mark/change')
    )
    asset_chart0 = models.FileField(
        blank=True, null=True, default=None, help_text='Asset',
        upload_to=UploadDataHeroImage('statement/ib/mark/asset0')
    )
    asset_chart1 = models.FileField(
        blank=True, null=True, default=None, help_text='Asset',
        upload_to=UploadDataHeroImage('statement/ib/mark/asset1')
    )

    def __unicode__(self):
        return '{change_value}'.format(
            change_value=self.change_value
        )


class IBMonthTradeOther(models.Model):
    ib_month = models.OneToOneField(IBMonthStatement)

    # hours filled
    hour_filled = models.CharField(
        max_length=50, help_text='Order filled hours chart tell you?', default='skew',
        choices=(
            ('mix', 'Mix - order filled hours is mix on every hours'),
            ('skew', 'Skew - order filled hours is skew to one single hour'),
            ('best', 'Best - order filled hour is mostly only on single hour'),
        )
    )
    hour_order = models.IntegerField(default=3, help_text='Optimize order hours filled')
    hour_chart = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/hour')
    )

    # unique symbols
    symbols = models.IntegerField(default=0, help_text='Unique symbols traded')

    # process cash
    cash_chart = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/cash')
    )

    # exchange
    exchange_chart = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/exchange')
    )

    # others stat
    trade_chart0 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/trade0')
    )
    trade_chart1 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/trade1')
    )
    trade_chart2 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/trade2')
    )


class IBMonthTradeExchange(models.Model):
    ib_month = models.ForeignKey(IBMonthStatement)

    exchange = models.CharField(max_length=50, default='')
    asset = models.CharField(
        max_length=50, default='stocks', choices=(
            ('stocks', 'Stocks'),
            ('options', 'Options'),
            ('others', 'Others'),
        )
    )
    trade = models.IntegerField(default=0, blank=True, help_text='trade filled')


class IBMonthTradeFee(models.Model):
    ib_month = models.OneToOneField(IBMonthStatement)

    # fee
    fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Monthly fee traded'
    )

    # fee by asset
    fee_stock = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Fee used for stocks'
    )
    fee_option = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Fee used for options'
    )
    fee_asset = models.CharField(
        max_length=50, help_text='Asset for traded order fee', default='balance',
        choices=(
            ('stock', 'Stock - most fee are use for trading stocks'),
            ('balance', 'Balance - almost 50/50 fee use on stocks & options'),
            ('option', 'Options - most fee are use for trading options'),
        )
    )

    # fee by enter/exit
    fee_enter = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Fee used when enter'
    )
    fee_exit = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Fee used when exit'
    )
    fee_timing = models.CharField(
        max_length=50, help_text='Traded order fee', default='balance',
        choices=(
            ('enter', 'Enter - most fee used when entering trade'),
            ('balance', 'Balance - 50/50 used for enter/exit trade'),
            ('exit', 'Exit - most fee used when exiting trade'),
        )
    )

    # fee by profit/loss
    fee_profit = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Fee used for profit trade'
    )
    fee_even = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Fee used for even trade'
    )
    fee_loss = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Fee used for loss trade'
    )
    fee_return = models.CharField(
        max_length=50, help_text='Traded order fee', default='even',
        choices=(
            ('profit', 'Profit - most fee used when closing profit trade'),
            ('even', 'Even - most fee used when entering even trade'),
            ('loss', 'Loss - most fee used when closing loss trade'),
        )
    )

    # charts
    fee_chart0 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/fee0')
    )
    fee_chart1 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/fee1')
    )
    fee_chart2 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/fee2')
    )
    fee_chart3 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/fee3')
    )
    fee_chart4 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/fee4')
    )
    fee_chart5 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/fee5')
    )
    fee_chart6 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/fee6')
    )

    def __unicode__(self):
        return '{fee}'.format(
            fee=self.fee
        )


class IBMonthTradeOrder(models.Model):
    ib_month = models.OneToOneField(IBMonthStatement)

    # order
    order = models.IntegerField(
        default=0, help_text='Monthly order traded'
    )

    # enter exit
    order_enter = models.IntegerField(default=0, blank=True, help_text='Enter order filled')
    order_exit = models.IntegerField(default=0, blank=True, help_text='Exit order filled')
    order_timing = models.CharField(
        max_length=50, help_text='Traded order', default='balance',
        choices=(
            ('enter', 'Enter - most order filled for entering trade'),
            ('balance', 'Balance - 50/50 order filled for enter/exit trade'),
            ('exit', 'Exit - most order filled for exiting trade'),
        )
    )

    # asset
    order_stock = models.IntegerField(default=0, blank=True, help_text='Stock order filled')
    order_option = models.IntegerField(default=0, blank=True, help_text='Options order filled')
    order_asset = models.CharField(
        max_length=50, help_text='Traded order asset', default='balance',
        choices=(
            ('stock', 'Stock - most order filled for stocks trade'),
            ('balance', 'Balance - 50/50 order filled for stock/options trade'),
            ('option', 'Options - most order filled for options trade'),
        )
    )

    # pl
    order_profit = models.IntegerField(default=0, blank=True, help_text='Profit order filled')
    order_loss = models.IntegerField(default=0, blank=True, help_text='Loss order filled')
    order_return = models.CharField(
        max_length=50, help_text='Traded order profit/loss', default='even',
        choices=(
            ('profit', 'Enter - most order filled for profit trade'),
            ('even', 'Balance - 50/50 order filled for profit/loss trade'),
            ('loss', 'Exit - most order filled for loss trade'),
        )
    )

    # charts
    order_chart0 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/order0')
    )
    order_chart1 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/order1')
    )
    order_chart2 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/order2')
    )
    order_chart3 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/order3')
    )
    order_chart4 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/order4')
    )


class IBMonthTradeReturn(models.Model):
    ib_month = models.OneToOneField(IBMonthStatement)

    # return
    trade_return = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text='Monthly return traded'
    )

    # return
    return_stock = models.IntegerField(default=0, blank=True, help_text='Stock return')
    return_option = models.IntegerField(default=0, blank=True, help_text='Options return')
    return_asset = models.CharField(
        max_length=50, help_text='Traded order return', default='balance',
        choices=(
            ('stock', 'Stock - most return by stocks trade'),
            ('balance', 'Balance - 50/50 return for stock/options trade'),
            ('option', 'Options - most return by options trade'),
        )
    )

    # stock
    stock_profit = models.IntegerField(default=0, blank=True, help_text='Profit stock order filled')
    stock_loss = models.IntegerField(default=0, blank=True, help_text='Loss stock order filled')
    stock_return = models.CharField(
        max_length=50, help_text='Traded stock order profit/loss', default='even',
        choices=(
            ('profit', 'Enter - most stock order filled for profit trade'),
            ('even', 'Balance - 50/50 stock order filled for profit/loss trade'),
            ('loss', 'Exit - most stock order filled for loss trade'),
        )
    )

    # option
    option_profit = models.IntegerField(default=0, blank=True, help_text='Profit options order filled')
    option_loss = models.IntegerField(default=0, blank=True, help_text='Loss options order filled')
    option_return = models.CharField(
        max_length=50, help_text='Traded options order profit/loss', default='even',
        choices=(
            ('profit', 'Enter - most options order filled for profit trade'),
            ('even', 'Balance - 50/50 options order filled for profit/loss trade'),
            ('loss', 'Exit - most options order filled for loss trade'),
        )
    )

    # charts
    return_chart0 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/return0')
    )
    return_chart1 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/return1')
    )
    return_chart2 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/return2')
    )
    return_chart3 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/return3')
    )
    return_chart4 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/return4')
    )


class IBMonthTradeDTE(models.Model):
    ib_month = models.OneToOneField(IBMonthStatement)

    # enter/exit by dte
    mean_enter = models.IntegerField(
        default=0, blank=True, help_text='Mean monthly enter DTE'
    )
    mean_exit = models.IntegerField(
        default=0, blank=True, help_text='Mean monthly enter DTE'
    )
    mean_timing = models.CharField(
        max_length=50, help_text='Order filled for dte', default='skew',
        choices=(
            ('mix', 'Mix - exit filled is mix on every dte'),
            ('skew', 'Skew - exit filled is skew to range dte'),
            ('best', 'Best - exit filled is mostly only on single hour'),
        )
    )

    # profit/loss exit by dte
    profit_exit = models.CharField(
        max_length=50, help_text='Profit filled by dte', default='middle',
        choices=(
            ('early', 'Early - exit filled mostly in early dte'),
            ('middle', 'Middle - exit filled mostly in middle dte'),
            ('late', 'Late - exit filled mostly in late dte'),
        )
    )
    loss_exit = models.CharField(
        max_length=50, help_text='Loss filled by dte', default='middle',
        choices=(
            ('early', 'Early - exit filled mostly in early dte'),
            ('middle', 'Middle - exit filled mostly in middle dte'),
            ('late', 'Late - exit filled mostly in late dte'),
        )
    )

    # charts
    dte_chart0 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/dte0')
    )
    dte_chart1 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/dte1')
    )
    dte_chart2 = models.FileField(
        blank=True, null=True, default=None, help_text='',
        upload_to=UploadDataHeroImage('statement/ib/trade/dte2')
    )


class IBMonthXrayNote(models.Model):
    """
    For Asset class allocation, country to sector
    better diversify your position and lower risk
    Using morningstar x-ray in TDA platform
    """
    ib_month = models.OneToOneField(IBMonthStatement)

    # usa stocks
    sector_note = models.TextField(
        default='', null=True, blank=True,
        help_text='Note from x-ray sector and your comment'
    )
    stock_note = models.TextField(
        default='', null=True, blank=True,
        help_text='Note from x-ray stock style and your comment'
    )
    type_note = models.TextField(
        default='', null=True, blank=True,
        help_text='Note from x-ray stock type and your comment'
    )

    # pdf
    report_pdf = models.FileField(
        blank=True, null=True, default=None, help_text='Report pdf',
        upload_to=UploadRenameImage('statement/ib/xray')
    )


class IBMonthXrayGlobal(models.Model):
    ib_month = models.OneToOneField(IBMonthStatement)

    # global diversify
    asset = models.CharField(
        max_length=50, help_text='What country or asset you invest in?', default='usa',
        choices=(
            ('cash', 'Cash - most of your capital invest in cash asset'),
            ('usa', 'USA - most of your capital invest in USA equity'),
            ('non_usa', 'Non-US - most of your capital invest in Non-us equity'),
            ('bond', 'Bond - most of your capital invest in bond'),
            ('others', 'Others - most of your capital invest in other asset'),
        )
    )
    region = models.CharField(
        max_length=50, help_text='', default='medium',
        choices=(
            ('high', 'High exposure risk - Bad diversify'),
            ('medium', 'Medium exposure risk - Normal diversify'),
            ('low', 'Low exposure risk - Well diversify'),
        )
    )

    asset_note = models.TextField(
        default='', null=True, blank=True,
        help_text='Note from x-ray and your comment'
    )
    region_note = models.TextField(
        default='', null=True, blank=True,
        help_text='Note from x-ray and your comment'
    )


class IBMonthXraySector(models.Model):
    ib_month = models.ForeignKey(IBMonthStatement)

    sector = models.CharField(
        max_length=50, help_text='', default='unknown',
        choices=(
            ('energy', 'Energy'),
            ('material', 'Materials'),
            ('industry', 'Industry'),
            ('discretionary', 'Consumer Discretionary'),
            ('staples', 'Consumer Staples'),
            ('health_care', 'Health Care'),
            ('financial', 'Financial'),
            ('technology', 'Information Technology'),
            ('telecom', 'Telecommunication Services'),
            ('Utilities', 'Utilities'),
            ('Real Estate', 'Real Estate'),
            ('unknown', 'Not classified'),
        )
    )

    exposure = models.CharField(
        max_length=50, help_text='', default='medium', blank=True,
        choices=(
            ('high', 'High exposure risk'),
            ('medium', 'Medium exposure risk'),
            ('low', 'Low exposure risk'),
        )
    )

    hold = models.FloatField(default=0, blank=True, help_text='Holding %')
    benchmark = models.FloatField(default=0, blank=True, help_text='Benchmark %')


class IBMonthXrayStockStyle(models.Model):
    ib_month = models.ForeignKey(IBMonthStatement)

    capital = models.CharField(
        max_length=50, help_text='Stock cap', default='large',
        choices=(
            ('large', 'Large cap'),
            ('medium', 'Medium cap'),
            ('small', 'Small cap'),
        )
    )

    style = models.CharField(
        max_length=50, help_text='Stock style', default='core',
        choices=(
            ('value', 'Value'),
            ('core', 'Core'),
            ('growth', 'Growth'),
        )
    )

    hold = models.FloatField(default=0, blank=True, help_text='Holding %')


class IBMonthXrayStockType(models.Model):
    ib_month = models.ForeignKey(IBMonthStatement)

    stock_type = models.CharField(
        max_length=50, help_text='', default='unknown',
        choices=(
            ('high_yield', 'High yield'),
            ('distressed', 'Distressed'),
            ('hard_asset', 'Hard asset'),
            ('cyclical', 'Cyclical'),
            ('slow_growth', 'Slow growth'),
            ('classic_growth', 'Classic growth'),
            ('speculative_growth', 'Speculative growth'),
            ('unknown', 'Unknown'),
        )
    )

    exposure = models.CharField(
        max_length=50, help_text='', default='medium',
        choices=(
            ('high', 'High exposure risk'),
            ('medium', 'Medium exposure risk'),
            ('low', 'Low exposure risk'),
        )
    )

    hold = models.FloatField(default=0, blank=True, help_text='Holding %')
    benchmark = models.FloatField(default=0, blank=True, help_text='Benchmark %')
