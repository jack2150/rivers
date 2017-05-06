import datetime
from django.db import models

from base.ufunc import UploadRenameImage


# moth
class MarketMonthEconomic(models.Model):
    """
    macro valuation, Weekly update
    """
    date = models.DateField(
        help_text='Monthly', unique=True,
        default=datetime.datetime.now,
    )

    # major economics indicator
    eco_cycle = models.CharField(
        choices=(
            ('bull', 'Bull - WLI growth > FIG inflate'),
            ('neutral', 'Neutral - WLI growth <= FIG inflate'),
            ('bear', 'Bear - WLI < FIG inflate'),
            ('jump', 'Jump - Sudden heavily increase in WLI >= FIG'),
            ('crash', 'Crash - Sudden large decrease in WLI & FIG'),
            ('unknown', 'Unknown - WLI or FIG shift heavily'),
        ),
        max_length=20, help_text='ECRI Economics cycle dashboard',
        default='neutral'
    )
    eco_index = models.CharField(
        choices=(
            ('bull', 'Bull - Leading up; coincident follow; lagging delay'),
            ('neutral', 'Neutral - Leading neutral; coincident same; lagging delay'),
            ('bear', 'Bear - Leading down; coincident follow; lagging delay'),
            ('crash', 'Crash - Leading crash; coincident neutral; lagging neutral'),
        ),
        max_length=20, help_text='ECRI leading/coincident/lagging index',
        default='neutral'
    )
    eco_chart0 = models.ImageField(
        blank=True, null=True, default=None, help_text='WLI & FIG',
        upload_to=UploadRenameImage('market/month/eco/main/')
    )
    eco_chart1 = models.ImageField(
        blank=True, null=True, default=None, help_text='Leading/coincident/lagging',
        upload_to=UploadRenameImage('market/month/eco/main/')
    )

    # top 3
    inflation = models.CharField(
        max_length=20, help_text='Inflation rate; M2:FRED', default='neutral',
        choices=(
            ('bull', 'Bull - inflation up, stock should up'),
            ('neutral', 'Neutral - inflation neutral, stock should neutral'),
            ('bear', 'Bear - inflation down, stock should down')
        ),
    )
    gdp = models.CharField(
        max_length=20, help_text='GDP; GDP:FRED', default='neutral',
        choices=(
            ('bull', 'Bull - total good & service value grow faster'),
            ('neutral', 'Neutral - total good & service value grow slowly'),
            ('bear', 'Bear - total good & service value decline')
        ),
    )
    employ = models.CharField(
        max_length=20, help_text='Unemployment rate; UNRATE:FRED', default='neutral',
        choices=(
            ('bull', 'Bull - decline unemployment rate. more people got job'),
            ('neutral', 'Neutral - stable unemployment rate'),
            ('bear', 'Bear - increase unemployment rate, moe people leave job')
        ),
    )
    top_chart0 = models.ImageField(
        blank=True, null=True, default=None, help_text='Inflation',
        upload_to=UploadRenameImage('market/month/eco/top/inflation')
    )
    top_chart1 = models.ImageField(
        blank=True, null=True, default=None, help_text='GDP',
        upload_to=UploadRenameImage('market/month/eco/top/gdp')
    )
    top_chart2 = models.ImageField(
        blank=True, null=True, default=None, help_text='Unemployment ate',
        upload_to=UploadRenameImage('market/month/eco/top/employ')
    )

    # major
    interest_rate = models.CharField(
        max_length=20, help_text='Interest Rate; INTDSRUSM193N:FRED', default='neutral',
        choices=(
            ('bull', 'Bull - interest rate rise, more money into USD & treasury/bond'),
            ('neutral', 'Neutral - interest rate un-change'),
            ('bear', 'Bear - interest rate drop, less money into USD & treasury/bond')
        ),
    )
    m2_supply = models.CharField(
        max_length=20, help_text='M2 Money stock; M2:FRED', default='neutral',
        choices=(
            ('bull', 'Bull - large increase in money to fund economics'),
            ('neutral', 'Neutral - Normal increase in money to keep economics going'),
            ('bear', 'Bear - low increase in money to budgeting economics')
        ),
    )
    trade_deficit = models.CharField(
        max_length=20, help_text='Trade Deficit; BOPGSTB:FRED', default='neutral',
        choices=(
            ('bull', 'Bear - more export than import, good economics'),
            ('neutral', 'Neutral - ranging export/import'),
            ('bear', 'Bull - less export than import, bad economics')
        ),
    )
    major_chart0 = models.ImageField(
        blank=True, null=True, default=None, help_text='Interest rate',
        upload_to=UploadRenameImage('market/month/eco/major/rate')
    )
    major_chart1 = models.ImageField(
        blank=True, null=True, default=None, help_text='M2 Money stock',
        upload_to=UploadRenameImage('market/month/eco/major/m2')
    )
    major_chart2 = models.ImageField(
        blank=True, null=True, default=None, help_text='Trade deficit',
        upload_to=UploadRenameImage('market/month/eco/major/trade_deficit')
    )

    # consumer
    cpi = models.CharField(
        max_length=20, help_text='Consumer Price Index; CPIAUCSL:FRED', default='neutral',
        choices=(
            ('bull', 'Bull - increase in price of good & service purchased'),
            ('neutral', 'Neutral - same price of good & service purchased'),
            ('bear', 'Bear - decline price of good & service purchased')
        ),
    )
    cc_survey = models.CharField(
        max_length=20, help_text='Consumer Confidence Survey; UMCSENT:FRED', default='neutral',
        choices=(
            ('bull', 'Bull - consumer are optimist, keep spending more'),
            ('neutral', 'Neutral - consumer think eco ok and have normal spend'),
            ('bear', 'Bear - consumer are pessimist, spend less & saving money')
        ),
    )
    retail_sale = models.CharField(
        max_length=20, help_text='US Retail Sales; RSXFS:FRED', default='neutral',
        choices=(
            ('bull', 'Bull - retail shop sell growth increase'),
            ('neutral', 'Neutral - retail shop sell is ok'),
            ('bear', 'Bear - retail shop sell decline')
        ),
    )
    house_start = models.CharField(
        max_length=20, help_text='Housing Starts; HOUST:FRED', default='neutral',
        choices=(
            ('bull', 'Bull - a lot of new house start building, good economics'),
            ('neutral', 'Neutral - normal range new house start building'),
            ('bear', 'Bear - less new house start building, bad economics')
        ),
    )
    consumer_chart0 = models.ImageField(
        blank=True, null=True, default=None, help_text='CPI',
        upload_to=UploadRenameImage('market/month/eco/consumer/cpi')
    )
    consumer_chart1 = models.ImageField(
        blank=True, null=True, default=None, help_text='Consumer survey',
        upload_to=UploadRenameImage('market/month/eco/consumer/cc_survey')
    )
    consumer_chart2 = models.ImageField(
        blank=True, null=True, default=None, help_text='Retail sale',
        upload_to=UploadRenameImage('market/month/eco/consumer/retail_sale')
    )
    consumer_chart3 = models.ImageField(
        blank=True, null=True, default=None, help_text='Housing start',
        upload_to=UploadRenameImage('market/month/eco/consumer/house_start')
    )

    # industry
    ppi = models.CharField(
        max_length=20, help_text='Producer Price Index', default='neutral',
        choices=(
            ('bull', 'Bull - selling price increase for domestic product'),
            ('neutral', 'Neutral - selling price stay range for domestic product'),
            ('bear', 'Bear - selling price decline for domestic product')
        ),
    )
    ipi = models.CharField(
        max_length=20, help_text='Industry Production Index; PPIACO:FRED', default='neutral',
        choices=(
            ('bull', 'Bull - industry produce more goods, good economics'),
            ('neutral', 'Neutral - industry produce same quantity of goods'),
            ('bear', 'Bear - industry produce less goods, bad economics')
        ),
    )
    biz_store = models.CharField(
        max_length=20, help_text='Total Business Inventories; ISRATIO:FRED', default='neutral',
        choices=(
            ('bull', 'Bull - company hold mass inventory, try to push more sale'),
            ('neutral', 'Neutral - company hold average inventory, so keep doing business'),
            ('bear', 'Bear - company reduce inventory, sale not going well')
        ),
    )
    corp_profit = models.CharField(
        max_length=20, help_text='Corporate Profits After Tax; CP:FRED', default='neutral',
        choices=(
            ('bull', 'Bull - company are making more profit, good market'),
            ('neutral', 'Neutral - company are making same average profit'),
            ('bear', 'Bear - company are making less profit, bad market')
        ),
    )
    wage = models.CharField(
        max_length=20, help_text='Average Weekly Earnings; CES0500000011:FRED', default='neutral',
        choices=(
            ('bull', 'Bull - worker earn more wage weekly, more to spend'),
            ('neutral', 'Neutral - worker earn average wage'),
            ('bear', 'Bear - worker earn less wage, less to spend')
        ),
    )
    product_chart0 = models.ImageField(
        blank=True, null=True, default=None, help_text='PPI',
        upload_to=UploadRenameImage('market/month/eco/dollar/ppi')
    )
    product_chart1 = models.ImageField(
        blank=True, null=True, default=None, help_text='Industry production index',
        upload_to=UploadRenameImage('market/month/eco/dollar/ipi')
    )
    product_chart2 = models.ImageField(
        blank=True, null=True, default=None, help_text='Business inventory',
        upload_to=UploadRenameImage('market/month/eco/product/biz_store')
    )
    product_chart3 = models.ImageField(
        blank=True, null=True, default=None, help_text='Corp profit after tax',
        upload_to=UploadRenameImage('market/month/eco/product/crop_profit')
    )
    product_chart4 = models.ImageField(
        blank=True, null=True, default=None, help_text='Weekly wage',
        upload_to=UploadRenameImage('market/month/eco/product/wage')
    )

    # currency
    dollar = models.CharField(
        max_length=20, help_text='Foreign Exchange Indicators', default='neutral',
        choices=(
            ('bull', 'Bull - USD currency in bullish, more money pull into market'),
            ('neutral', 'Neutral - USD currency in sideway, no impact on market'),
            ('bear', 'Bear - USD currency in bearish, money are out USA market')
        ),
    )
    dollar_chart0 = models.ImageField(
        blank=True, null=True, default=None, help_text='EUR/USD',
        upload_to=UploadRenameImage('market/month/eco/dollar/eur')
    )
    dollar_chart1 = models.ImageField(
        blank=True, null=True, default=None, help_text='USD/CAD',
        upload_to=UploadRenameImage('market/month/eco/dollar/cad')
    )
    dollar_chart2 = models.ImageField(
        blank=True, null=True, default=None, help_text='USD/JPY',
        upload_to=UploadRenameImage('market/month/eco/dollar/jpy')
    )
    dollar_chart3 = models.ImageField(
        blank=True, null=True, default=None, help_text='USD/CNH',
        upload_to=UploadRenameImage('market/month/eco/dollar/cnh')
    )
    dollar_chart4 = models.ImageField(
        blank=True, null=True, default=None, help_text='Dollar',
        upload_to=UploadRenameImage('market/month/eco/dollar/usd')
    )

    # policy
    monetary = models.TextField(
        null=True, blank=True, help_text='Monetary policy simple explanation'
    )
    commentary = models.TextField(
        null=True, blank=True, help_text='Write down what important next month'
    )
    policy_report = models.FileField(
        blank=True, null=True, default=None, help_text='Major policy',
        upload_to=UploadRenameImage('market/month/eco/policy')
    )

    # eco stage
    bubble_stage = models.CharField(
        max_length=20, help_text='Market fair value', default='new_era',
        choices=(
            ('birth', 'The birth of a boom - some sector, other sector down'),
            ('breed', 'The breed of a bubble - rate low, credit grow, company increase profit'),
            ('new_era', 'Everyone buy new ara - always go up, valuation standard abandon'),
            ('distress', 'Financial distress - insider cash out, excess leverage, fraud detected'),
            ('scare', 'Financial scare - investor scare, no longer trade in market'),
        ),
    )
    market_scenario = models.CharField(
        max_length=20, help_text='Inflation, Rates, and Stock', default='positive',
        choices=(
            ('very_negative', 'Very Negative - interest+, inflation+, stock-, cash-'),
            ('midly_negative', 'Midly Negative - interest+, inflation+, stock-, cash+'),
            ('positive', 'Positive - rate+, inflation+, stock+, sale+')
        )
    )

    def __unicode__(self):
        return 'MonthEconomic {date}'.format(
            date=self.date
        )


# week
class MarketWeek(models.Model):
    date = models.DateField(unique=True, help_text='Weekly')

    commentary = models.TextField(
        default='Write down weekly comment & expectation', null=True, blank=True
    )

    def __unicode__(self):
        return 'MarketWeek {date}'.format(
            date=self.date
        )


# fund relocation
class MarketWeekRelocation(models.Model):
    """
    Asset relocation
    """
    market_week = models.OneToOneField(MarketWeek, null=True, default=None)

    tlt = models.BooleanField(default=False, help_text='Buy more bond than stock?')
    gld = models.BooleanField(default=False, help_text='Buy more gold than stock?')
    veu = models.BooleanField(default=False, help_text='Buy more global than stock?')
    eem = models.BooleanField(default=False, help_text='Buy more global than stock?')

    chart_image = models.ImageField(
        blank=True, null=True, default=None, help_text='SPY to TLT/GLD/VEU/EEM ratio',
        upload_to=UploadRenameImage('market/week/relocation'),
    )


# sector
class MarketWeekSector(models.Model):
    """
    Sector weight & movement
    """
    market_week = models.OneToOneField(MarketWeek, null=True, default=None)

    join_chart = models.ImageField(
        blank=True, null=True, default=None, help_text='Sector chart (mix)',
        upload_to=UploadRenameImage('market/week/sector/main0'),
    )
    week_chart = models.ImageField(
        blank=True, null=True, default=None, help_text='Sector chart (mix)',
        upload_to=UploadRenameImage('market/week/sector/main1'),
    )
    weight_chart = models.ImageField(
        blank=True, null=True, default=None, help_text='Sector weight report',
        upload_to=UploadRenameImage('market/week/sector/weight/chart'),
    )
    weight_report = models.FileField(
        blank=True, null=True, default=None, help_text='Sector weight report',
        upload_to=UploadRenameImage('market/week/sector/weight/report'),
    )


class MarketWeekSectorItem(models.Model):
    market_week = models.ForeignKey(MarketWeek, null=True, default=None)

    name = models.CharField(
        choices=(
            ('xly', 'XLY - Consumer discretionary'),
            ('xlp', 'XLP - Consumer staples'),
            ('xle', 'XLE - Energy'),
            ('xlf', 'XLF - Financial'),
            ('xlv', 'XLV - Healthcare'),
            ('xli', 'XLI - Industry'),
            ('xlb', 'XLB - Material'),
            ('xlre', 'XLRE - Real estate'),
            ('xlk', 'XLK - Technology'),
            ('xlu', 'XLU - Utility'),
        ),
        max_length=20, help_text='Sector name'
    )
    weight = models.CharField(
        choices=(
            ('over', 'Overweight'),
            ('market', 'Marketweight'),
            ('under', 'Underweight'),
        ),
        max_length=20, help_text='Sector weight', default='market'
    )
    grade = models.CharField(
        choices=(
            ('upgrade', 'Upgrade'),
            ('neutral', 'Neutral'),
            ('downgrade', 'Downgrade'),
        ),
        max_length=20, help_text='Sector weight change', default='neutral'
    )
    change = models.FloatField(default=0, help_text='Weight change in %')
    move = models.CharField(
        choices=(
            ('bull', 'Bull - price move breakout last week range'),
            ('neutral', 'Neutral - price move within last week range'),
            ('bear', 'Bear - price move breakdown last week range'),
        ),
        max_length=20, help_text='Sector move', default='neutral'
    )
    chart = models.ImageField(
        blank=True, null=True, default=None, help_text='Sector chart',
        upload_to=UploadRenameImage('market/week/sector/sub'),
    )

    unique_together = (('market_week', 'name'),)


# indices
class MarketWeekIndices(models.Model):
    market_week = models.ForeignKey(MarketWeek, null=True, default=None)

    name = models.CharField(
        choices=(
            ('spy', 'SPY - S&P 500'),
            ('qqq', 'QQQ - Nasdaq 100'),
            ('dia', 'DIA - Dow Jones'),
            ('iwm', 'IWM - Russell 2000'),
        ),
        max_length=20, help_text='Indices name'
    )
    change = models.FloatField(default=0, help_text='Weight change in %')
    move = models.CharField(
        choices=(
            ('bull', 'Bull - price move breakout last week range'),
            ('neutral', 'Neutral - price move within last week range'),
            ('bear', 'Bear - price move breakdown last week range'),
        ),
        max_length=20, help_text='Indices move', default='neutral'
    )
    chart = models.ImageField(
        blank=True, null=True, default=None, help_text='Sector chart',
        upload_to=UploadRenameImage('market/week/indices'),
    )
    resistant = models.FloatField(default=0, help_text='Weekly resistant')
    support = models.FloatField(default=0, help_text='Weekly support')

    unique_together = (('market_week', 'name'),)


class MarketWeekCommodity(models.Model):
    market_week = models.ForeignKey(MarketWeek, null=True, default=None)

    name = models.CharField(
        choices=(
            ('uso', 'USO - Crude oil'),
            ('ung', 'UNG - Natural gas'),
            ('gld', 'GLD - Gold'),
            ('tlt', 'TLT - Bond 30 years'),
            ('shy', 'SHY - Bond 2 years'),
            ('uup', 'UUP - USD dollar'),

            ('dba', 'DBA - Grain & soft'),
            ('cow', 'COW - Meat'),
        ),
        max_length=20, help_text='Commodity name'
    )
    change = models.FloatField(default=0, help_text='% change', blank=True)
    move = models.CharField(
        choices=(
            ('bull', 'Bull - price move breakout last week range'),
            ('neutral', 'Neutral - price move within last week range'),
            ('bear', 'Bear - price move breakdown last week range'),
        ),
        max_length=20, help_text='Sector move', default='neutral', blank=True
    )
    chart = models.ImageField(
        blank=True, null=True, default=None, help_text='Sector chart',
        upload_to=UploadRenameImage('market/week/commodity'),
    )

    unique_together = (('market_week', 'name'),)


# Global
class MarketWeekGlobal(models.Model):
    market_week = models.ForeignKey(MarketWeek, null=True, default=None)

    name = models.CharField(
        choices=(
            ('america', 'ILF - Latin America'),
            ('europe', 'VGK - Europe'),
            ('asia', 'VPL - Asia'),
            ('africa', 'EZA - Africa'),
            ('australia', 'EWA - Australia'),
        ),
        max_length=20, help_text='Global name'
    )
    weight = models.CharField(
        choices=(
            ('over', 'Overweight'),
            ('market', 'Marketweight'),
            ('under', 'Underweight'),
        ),
        max_length=20, help_text='Global weight', default='market', blank=True
    )
    change = models.FloatField(default=0, help_text='% change', blank=True)
    move = models.CharField(
        choices=(
            ('bull', 'Bull - price move breakout last week range'),
            ('neutral', 'Neutral - price move within last week range'),
            ('bear', 'Bear - price move breakdown last week range'),
        ),
        max_length=20, help_text='Global move', default='neutral', blank=True
    )
    chart = models.ImageField(
        blank=True, null=True, default=None, help_text='Global chart',
        upload_to=UploadRenameImage('market/week/global'),
    )

    unique_together = (('market_week', 'name'),)


class MarketWeekCountry(models.Model):
    market_week = models.ForeignKey(MarketWeek, null=True, default=None)

    name = models.CharField(
        choices=(
            ('england', 'EWU - England'),
            ('germany', 'EWG - Germany'),
            ('russia', 'RSX - Russia'),
            ('mexico', 'EWW - Mexico'),
            ('brazil', 'EWZ - Brazil'),
            ('japan', 'EWJ - Japan'),
            ('china', 'FXI - China'),
            ('malaysia', 'EWM - Malaysia'),
        ),
        max_length=20, help_text='Country name'
    )
    weight = models.CharField(
        choices=(
            ('over', 'Overweight'),
            ('market', 'Marketweight'),
            ('under', 'Underweight'),
        ),
        max_length=20, help_text='Country weight', default='market', blank=True
    )
    grade = models.CharField(
        choices=(
            ('upgrade', 'Upgrade'),
            ('neutral', 'Neutral'),
            ('downgrade', 'Downgrade'),
        ),
        max_length=20, help_text='Country weight change', default='neutral', blank=True
    )
    change = models.FloatField(default=0, help_text='% change', blank=True)
    move = models.CharField(
        choices=(
            ('bull', 'Bull - price move breakout last week range'),
            ('neutral', 'Neutral - price move within last week range'),
            ('bear', 'Bear - price move breakdown last week range'),
        ),
        max_length=20, help_text='Country move', default='neutral', blank=True
    )
    chart = models.ImageField(
        blank=True, null=True, default=None, help_text='Country chart',
        upload_to=UploadRenameImage('market/week/country'),
    )

    unique_together = (('market_week', 'name'),)


# technical chart (SPY)
class MarketWeekTechnical(models.Model):
    market_week = models.ForeignKey(MarketWeek, null=True, default=None)

    symbol = models.CharField(max_length=20, default='', help_text='Symbol')
    name = models.CharField(
        choices=(
            ('price', 'Price'),
            ('volume', 'Volume'),
            ('cyclical', 'Cyclical'),
            ('momentum', 'Momentum'),
            ('sentiment', 'Sentiment'),
            ('strength', 'Strength'),
            ('others', 'Others'),
        ),
        max_length=20, help_text='Technical category', default='others'
    )
    title = models.CharField(max_length=200, default='')
    direction = models.CharField(
        choices=(('bull', 'Bull'), ('neutral', 'Neutral'), ('bear', 'Bear')),
        max_length=20, default='neutral', help_text='Expect direction'
    )
    chart0 = models.ImageField(
        blank=True, null=True, default=None,
        upload_to=UploadRenameImage('market/week/technical'),
        help_text='Chart/graph with explanation'
    )
    chart1 = models.ImageField(
        blank=True, null=True, default=None,
        upload_to=UploadRenameImage('market/week/technical'),
        help_text='Chart/graph with explanation'
    )
    chart2 = models.ImageField(
        blank=True, null=True, default=None,
        upload_to=UploadRenameImage('market/week/technical'),
        help_text='Chart/graph with explanation'
    )
    chart3 = models.ImageField(
        blank=True, null=True, default=None,
        upload_to=UploadRenameImage('market/week/technical'),
        help_text='Chart/graph with explanation'
    )
    chart4 = models.ImageField(
        blank=True, null=True, default=None,
        upload_to=UploadRenameImage('market/week/technical'),
        help_text='Chart/graph with explanation'
    )

    desc = models.TextField(
        default='', null=True, blank=True, help_text='Explanation'
    )


# sentiment
class MarketWeekFund(models.Model):
    market_week = models.OneToOneField(MarketWeek, null=True, default=None)

    # section: Contrary-Opinion Rules
    margin_debt = models.CharField(
        choices=(
            ('buy', 'High - borrow a lot buy'),
            ('hold', 'Normal - borrow to buy'),
            ('sell', 'Low - borrow less to buy'),
        ),
        max_length=20, help_text='Margin debt'
    )  # investor borrow more: higher, stock up; borrow less: lower, stock down
    # credit balance lower: investor buy, higher: investor sell
    credit_balance = models.CharField(
        choices=(
            ('buy', 'Low - invest in stock'),
            ('sell', 'High - invest in bond'),
        ),
        max_length=20, help_text='Market credit balance'
    )  # bond conf index, higher: invest in bond, lower: invest in stock
    confidence_index = models.CharField(
        choices=(
            ('buy', 'High - buy stock, sell bond yield bad'),
            ('hold', 'Normal - buy stock, buy bond'),
            ('sell', 'Low - sell stock, buy bond yield good'),
        ),
        max_length=20, help_text='Confidence Index'
    )


class MarketWeekFundNetCash(models.Model):
    market_week = models.ForeignKey(MarketWeek, null=True, default=None)

    name = models.CharField(
        choices=(
            ('stock', 'Stock fund'),
            ('hybrid', 'Hybrid fund'),
            ('tax_bond', 'Tax bond'),
            ('muni_bond', 'Muni bond'),
            ('money', 'Money market')
        ),
        max_length=20, help_text='Fund category'
    )
    value_chg = models.FloatField(
        default=0, blank=True, help_text='value change (Mil)'
    )
    total_asset = models.FloatField(
        default=0, blank=True, help_text='total asset (Bil or 1000 Mil)'
    )
    signal = models.CharField(
        choices=(
            ('strong_buy', 'Strong buy - manager aggressive buying'),
            ('buy', 'Buy - manager are slowly buying'),
            ('hold', 'Hold - manager holding'),
            ('sell', 'Sell - manager are slowly selling'),
            ('strong_sell', 'Strong sell - manager aggressive selling')
        ),
        max_length=20, help_text='Stock net new cash flow', default='hold', blank=True
    )

    def __unicode__(self):
        return '{name} {change}%'.format(
            name=self.name, change=('%.2f' % float(self.value_chg/self.total_asset))
        )


class MarketWeekCommitment(models.Model):
    market_week = models.ForeignKey(MarketWeek, null=True, default=None)

    name = models.CharField(
        choices=(
            ('sp500', 'S&P 500'),
            ('nasdaq', 'Nasdaq 100'),
            ('djia', 'DJIA'),
            ('rs2000', 'Russell 2000'),
            ('oil', 'Crude oil'),
            ('gas', 'Natural gas'),
            ('gold', 'Gold'),
            ('bond30y', 'Bond 30 years'),
            ('bond2y', 'Bond 2 years'),
            ('dollar', 'USD dollar'),
        ),
        max_length=20, help_text='Country name'
    )
    open_interest = models.IntegerField(default=0, blank=True)
    change = models.IntegerField(default=0, blank=True)
    trade = models.IntegerField(default=0, blank=True)

    signal = models.CharField(
        choices=(
            ('strong_buy', 'Strong buy - trader borrow to buy'),
            ('buy', 'Buy - trader are buying'),
            ('hold', 'Hold - trader have mix buy/sell'),
            ('sell', 'Sell - trader are selling'),
            ('strong_sell', 'Strong sell - trader sell and keep cash'),
        ),
        max_length=20, help_text='CFTC trader (check volume)', default='hold', blank=True
    )


class MarketWeekSentiment(models.Model):
    market_week = models.OneToOneField(MarketWeek, null=True, default=None)

    # from cnn money
    sentiment_index = models.CharField(
        choices=(
            ('ex_greed', 'Extreme Greed'), ('greed', 'Greed'), ('neutral', 'Neutral'),
            ('fear', 'Fear'), ('ex_fear', 'Extreme Fear')
        ),
        max_length=20, help_text='% Bull-Bear Spread', default='neutral'
    )  # greek: move up, fear: move down
    put_call_ratio = models.CharField(
        choices=(
            ('ex_greed', 'Extreme Greed'), ('greed', 'Greed'), ('neutral', 'Neutral'),
            ('fear', 'Fear'), ('ex_fear', 'Extreme Fear')
        ),
        max_length=20, help_text='Market put call ratio', default='neutral'
    )  # market put call buy ratio, higher: more call, bull, lower: more put, bear
    market_momentum = models.CharField(
        choices=(
            ('ex_greed', 'Extreme Greed'), ('greed', 'Greed'), ('neutral', 'Neutral'),
            ('fear', 'Fear'), ('ex_fear', 'Extreme Fear')
        ),
        max_length=20, help_text='Market momentum', default='neutral'
    )
    junk_bond_demand = models.CharField(
        choices=(
            ('ex_greed', 'Extreme Greed'), ('greed', 'Greed'), ('neutral', 'Neutral'),
            ('fear', 'Fear'), ('ex_fear', 'Extreme Fear')
        ),
        max_length=20, help_text='Junk bond demand', default='neutral'
    )
    price_strength = models.CharField(
        choices=(
            ('ex_greed', 'Extreme Greed'), ('greed', 'Greed'), ('neutral', 'Neutral'),
            ('fear', 'Fear'), ('ex_fear', 'Extreme Fear')
        ),
        max_length=20, help_text='Price strength', default='neutral'
    )
    safe_heaven_demand = models.CharField(
        choices=(
            ('ex_greed', 'Extreme Greed'), ('greed', 'Greed'), ('neutral', 'Neutral'),
            ('fear', 'Fear'), ('ex_fear', 'Extreme Fear')
        ),
        max_length=20, help_text='Safe heaven demand', default='neutral'
    )
    market_volatility = models.CharField(
        choices=(
            ('ex_greed', 'Extreme Greed'), ('greed', 'Greed'), ('neutral', 'Neutral'),
            ('fear', 'Fear'), ('ex_fear', 'Extreme Fear')
        ),
        max_length=20, help_text='Market volatility', default='neutral'
    )
    index_image = models.ImageField(
        blank=True, null=True, default=None, help_text='Sentiment index',
        upload_to=UploadRenameImage('market/week/sentiment/index'),
    )
    index_chart = models.ImageField(
        blank=True, null=True, default=None, help_text='Sentiment chart',
        upload_to=UploadRenameImage('market/week/sentiment/chart'),
    )


class MarketWeekValuation(models.Model):
    market_week = models.OneToOneField(MarketWeek, null=True, default=None)

    # third party
    sentiment = models.CharField(
        choices=(
            ('ex_greed', 'Extreme Greed - A lot more % Bull than Bear Spread'),
            ('greed', 'Greed - More % Bull than Bear Spread'),
            ('neutral', 'Neutral - Balance between % Bull & Bear Spread'),
            ('fear', 'Fear - Less % Bull than Bear Spread'),
            ('ex_fear', 'Extreme Fear - Very few % Bull and a lot Bear Spread')
        ),
        max_length=20, help_text='Investor sentiment - % Bull-Bear Spread', default='neutral'
    )

    # t-bill eurodollar spread,
    # higher: money into t-bill, stock down,
    # lower: money out t-bill, stock up
    # lower: investor sell, higher: investor buy
    ted_spread = models.CharField(
        choices=(
            ('buy', 'Low - money sell t-bil, buy stock'),
            ('hold', 'Normal - money buy t-bill, buy stock'),
            ('sell', 'High - money buy t-bill, sell stock')
        ),
        max_length=20, help_text='Ted spread', default='hold'
    )
    # section: market momentum
    # Breadth of Market: high, more advance price, stock up; low, more decline price, stock down
    market_breadth = models.CharField(
        choices=(
            ('buy', 'Advances - more buy tick than sell tick'),
            ('hold', 'In range - buy tick and sell tick almost same'),
            ('sell', 'Declines - less buy tick than sell tick'),
        ),
        max_length=20, help_text='Breadth of Market', default='hold'
    )
    # below 20: oversold, above: 80 overbought
    ma200day_pct = models.CharField(
        choices=(
            ('buy', 'Overbought'),
            ('hold', 'Fair value'),
            ('sell', 'Oversold')
        ),
        max_length=20, help_text='% of S&P 500 Stocks > 200-Day SMA', default='hold'
    )

    # $trin, Short-Term Trading Index: overbought: sell, oversold: buy
    arms_index = models.CharField(
        choices=(
            ('sell', 'High - overbought'),
            ('hold', 'Middle - fair value'),
            ('buy', 'Low - oversold'),
        ),
        max_length=20, help_text='Short-Term Trading Arms Index', default='hold'
    )

    # market fair value, undervalue: buy, overvalue: sell
    fair_value = models.CharField(
        choices=(
            ('buy', 'High - overbought'),
            ('hold', 'Middle - fair value'),
            ('sell', 'Low - oversold')
        ),
        max_length=20, help_text='Market fair value', default='hold'
    )

    chart0 = models.ImageField(
        blank=True, null=True, default=None, help_text='sentiment',
        upload_to=UploadRenameImage('market/week/valuation/sentiment'),
    )
    chart1 = models.ImageField(
        blank=True, null=True, default=None, help_text='ted_spread',
        upload_to=UploadRenameImage('market/week/valuation/ted_spread'),
    )
    chart2 = models.ImageField(
        blank=True, null=True, default=None, help_text='market_breadth',
        upload_to=UploadRenameImage('market/week/valuation/market_breadth'),
    )
    chart3 = models.ImageField(
        blank=True, null=True, default=None, help_text='ma200day_pct',
        upload_to=UploadRenameImage('market/week/valuation/ma200day_pct'),
    )
    chart4 = models.ImageField(
        blank=True, null=True, default=None, help_text='arms_index',
        upload_to=UploadRenameImage('market/week/valuation/arms_index'),
    )
    chart5 = models.ImageField(
        blank=True, null=True, default=None, help_text='fair_value',
        upload_to=UploadRenameImage('market/week/valuation/fair_value'),
    )


# impl vol
class MarketWeekImplVol(models.Model):
    market_week = models.OneToOneField(MarketWeek)

    move = models.CharField(
        choices=(
            ('bull', 'Bull - spike up; a lot protection are bought'),
            ('neutral', 'Neutral - ranging; not much protection that trade'),
            ('bear', 'Bear - spike down; protection are sold'),
        ),
        max_length=20, default='neutral', help_text='Vix movement'
    )
    resist = models.FloatField(default=0, help_text='Vix resistant')
    support = models.FloatField(default=0, help_text='Vix support')

    chart = models.ImageField(
        blank=True, null=True, default=None, help_text='ImplVol chart',
        upload_to=UploadRenameImage('market/week/impl_vol'),
    )


# report research & article
class MarketWeekResearch(models.Model):
    market_week = models.ForeignKey(MarketWeek, null=True, default=None)

    source = models.CharField(
        choices=(
            ('web', 'Web or Video'),
            ('schwab', 'Charles Schwab'),
            ('jpm', 'JP Morgan'),
            ('blk', 'Black Rock'),
            ('tda', 'TD Ameritrade'),
        ),
        max_length=20, help_text='Article source', default=''
    )
    expect = models.CharField(
        choices=(('bull', 'Bull'), ('neutral', 'Neutral'), ('bear', 'Bear')),
        max_length=20, help_text='Expect market direction', default='neutral'
    )
    comment = models.TextField(
        default='', blank=True, null=True, help_text='Commentary'
    )
    report = models.FileField(
        blank=True, null=True, default=None, help_text='Report pdf',
        upload_to=UploadRenameImage('market/week/research'),
    )


class MarketWeekArticle(models.Model):
    market_week = models.ForeignKey(MarketWeek, null=True, default=None)

    date = models.DateField(default=datetime.datetime.now)
    link = models.CharField(max_length=2000, help_text='article source')
    name = models.CharField(max_length=500, help_text='article title')
    category = models.CharField(
        help_text='Type of article', max_length=20, default='review',
        choices=(('review', 'Review'), ('analysis', 'Analysis'), ('general', 'General'))
    )
    chance = models.CharField(
        help_text='Chance of happen', max_length=20, default='low',
        choices=(('low', 'Low'), ('medium', 'Medium'), ('high', 'High'))
    )
    key_point = models.TextField(help_text='Main point & extra attention')


# day
# eco calendar
class MarketDayEconomic(models.Model):
    market_week = models.ForeignKey(MarketWeek)

    date = models.DateField(
        null=True, default=datetime.datetime.now, help_text='Bday', unique=True
    )

    market_indicator = models.IntegerField(default=0)
    extra_attention = models.IntegerField(default=0)
    key_indicator = models.IntegerField(default=0)
    special_news = models.BooleanField(default=False)

    news = models.TextField(default='', null=True, blank=True)


class MarketWeekEtfFlow(models.Model):
    market_week = models.ForeignKey(MarketWeek)

    asset = models.CharField(
        choices=(
            ('us_equity', 'U.S. Equity'),
            ('world_equity', 'International Equity'),
            ('us_bond', 'U.S. Fixed Income'),
            ('world_bond', 'International Fixed Income'),
            ('commodity', 'Commodities'),
            ('currency', 'Currency'),
            ('leveraged', 'Leveraged'),
            ('inverse', 'Inverse'),
            ('allocation', 'Asset Allocation'),
            ('alternative', 'Alternatives'),
        ),
        max_length=50, help_text=''
    )
    pct_aum = models.FloatField(
        default=0, help_text='% of AUM', blank=True
    )
    move = models.CharField(
        choices=(
            ('bull', 'Bull - price move breakout last week range'),
            ('neutral', 'Neutral - price move within last week range'),
            ('bear', 'Bear - price move breakdown last week range'),
        ),
        max_length=20, help_text='Sector move', default='neutral', blank=True
    )


# month to week decision
class MarketStrategy(models.Model):
    date = models.DateField(help_text='Weekly', unique=True, default=datetime.datetime.today)

    economic = models.CharField(
        choices=(
            ('good', 'Good - economics is making higher'),
            ('normal', 'Neutral - economics move sideway'),
            ('bad', 'Bad - economics is moving lower'),
        ),
        max_length=20, help_text='Economics condition (report)'
    )
    week_movement = models.CharField(
        choices=(
            ('bull', 'Bull - market bullish; making higher'),
            ('neutral', 'Neutral - market neutral; trading in range'),
            ('bear', 'Bear - market bearish; making lower'),
        ),
        max_length=50, help_text='Month to week market movement (expectation)'
    )

    def __unicode__(self):
        return 'MarketStrategy {date}'.format(
            date=self.date
        )


class MarketStrategyOpportunity(models.Model):
    market_strategy = models.ForeignKey(MarketStrategy)

    name = models.CharField(
        choices=(
            ('buy', 'Buy - good economics, market bull; embrace, keep buy'),
            ('hold', 'Hold - good economics, market neutral; buy support & sell resist'),
            ('strong_buy', 'Strong buy - good economics, market bear; collect, aggressive buy'),
            ('hold', 'Hold - normal economics, market bull; ignore, wait for opportunity'),
            ('hold', 'Hold - normal economics, market neutral; buy support & sell resist'),
            ('buy', 'Hold - normal economics, market bear; caution buy'),
            ('strong_sell', 'Strong sell - bad economics, market bull; reject, aggressive short'),
            ('hold', 'Hold - bad economics, market neutral; buy support & sell resist'),
            ('sell', 'Sell - bad economics, market bear; follow, caution short'),
        ),
        max_length=50, help_text='Opportunity'
    )
    resist = models.FloatField(default=0, blank=True)
    support = models.FloatField(default=0, blank=True)

    unique_together = (('week_strategy', 'name'), )


class MarketStrategyAllocation(models.Model):
    market_strategy = models.ForeignKey(MarketStrategy)

    name = models.CharField(
        choices=(
            ('usa_large', 'USA - Money in USA over World; large over small cap'),
            ('usa_small', 'USA - Money in USA over World; small over large cap'),
            ('usa_bond', 'USA - Money in USA over World; in Bond, not stock'),
            ('world_stock', 'World - Money in World over USA; Worldwide equity'),
            ('world_bond', 'World - Money in World over USA; Worldwide bond'),
            ('others', 'Others - like REIT, material, commodity and etc')
        ),
        max_length=50, help_text='Money flow allocation'
    )

    focus = models.TextField(default='', blank=True)
    ignore = models.TextField(default='', blank=True)

    unique_together = (('week_strategy', 'name'),)


class MarketStrategyDistribution(models.Model):
    market_strategy = models.ForeignKey(MarketStrategy)

    name = models.CharField(
        choices=(
            ('primary', 'Primary distribution'),
            ('secondary', 'Secondary distribution'),
            ('others', 'Others distribution'),
        ),
        max_length=50, help_text='Distribution, total 10 positions'
    )

    long_pos = models.IntegerField(default=0, help_text='Long position')
    neutral_long_pos = models.IntegerField(default=0, help_text='Neutral to Long position')
    neutral_pos = models.IntegerField(default=10, help_text='Neutral position')
    neutral_short_pos = models.IntegerField(default=0, help_text='Neutral to short position')
    short_pos = models.IntegerField(default=0, help_text='Short position')

    weight = models.BooleanField(default=False, help_text='Follow sector weighting?')

    unique_together = (('week_strategy', 'name'),)





