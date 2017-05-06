from django.contrib import admin
from django.core.urlresolvers import reverse
from opinion.group.market.models import *
from opinion.group.report.admin import OpinionStackedAdmin, OpinionAdmin


class MarketMonthEconomicAdmin(OpinionAdmin):
    def market_review(self, obj):
        return '<a href="{link}">Link</a> | <a href="{report}">Report</a>'.format(
            link=reverse('market_month_economic_create', kwargs={'obj_id': obj.id}),
            report=reverse('market_month_report', kwargs={'obj_id': obj.id})
        )

    market_review.allow_tags = True
    market_review.short_description = ''

    list_display = (
        'date', 'eco_cycle', 'eco_index', 'market_review'
    )

    fieldsets = (
        ('Primary', {
            'fields': ('date',)
        }),
        ('Economics', {
            'fields': (
                'eco_cycle', 'eco_index', 'eco_chart0', 'eco_chart1'
            )
        }),
        ('Top 3', {
            'fields': (
                'inflation', 'gdp', 'employ', 'top_chart0', 'top_chart1', 'top_chart2'
            )
        }),
        ('Major', {
            'fields': (
                'interest_rate', 'm2_supply', 'trade_deficit',
                'major_chart0', 'major_chart1', 'major_chart2'
            )
        }),
        ('Consumer', {
            'fields': (
                'cpi', 'cc_survey', 'retail_sale', 'house_start',
                'consumer_chart0', 'consumer_chart1', 'consumer_chart2', 'consumer_chart3'
            )
        }),
        ('Manufacture', {
            'fields': (
                'ppi', 'ipi', 'biz_store', 'corp_profit', 'wage',
                'product_chart0', 'product_chart1', 'product_chart2', 'product_chart3',
                'product_chart4'
            )
        }),
        ('Currency', {
            'fields': (
                'dollar',
                'dollar_chart0', 'dollar_chart1', 'dollar_chart2', 'dollar_chart3',
                'dollar_chart4'
            )
        }),
        ('Policy', {
            'fields': (
                'monetary', 'commentary', 'policy_report'
            )
        }),
        ('State', {
            'fields': (
                'bubble_stage', 'market_scenario'
            )
        }),
    )

    search_fields = ('date',)
    list_per_page = 20


class MarketWeekRelocationInline(admin.TabularInline):
    model = MarketWeekRelocation


class MarketWeekSectorAdmin(admin.TabularInline):
    model = MarketWeekSector


class MarketWeekSectorItemAdmin(admin.TabularInline):
    model = MarketWeekSectorItem
    extra = 0


class MarketWeekIndicesAdmin(admin.TabularInline):
    model = MarketWeekIndices
    extra = 0


class MarketWeekCommodityAdmin(admin.TabularInline):
    model = MarketWeekCommodity
    extra = 0


class MarketWeekGlobalAdmin(admin.TabularInline):
    model = MarketWeekGlobal
    extra = 0


class MarketWeekCountryAdmin(admin.TabularInline):
    model = MarketWeekCountry
    extra = 0


class MarketWeekTechnicalAdmin(OpinionStackedAdmin):
    model = MarketWeekTechnical
    extra = 0


class MarketWeekFundAdmin(admin.TabularInline):
    model = MarketWeekFund


class MarketWeekFundNetCashAdmin(admin.TabularInline):
    model = MarketWeekFundNetCash
    extra = 0


class MarketWeekSentimentAdmin(admin.TabularInline):
    model = MarketWeekSentiment


class MarketWeekCommitmentAdmin(admin.TabularInline):
    model = MarketWeekCommitment
    extra = 0


class MarketWeekValuationAdmin(OpinionStackedAdmin):
    model = MarketWeekValuation


class MarketWeekImplVolAdmin(admin.TabularInline):
    model = MarketWeekImplVol


class MarketWeekResearchInline(admin.TabularInline):
    model = MarketWeekResearch
    extra = 0


class MarketWeekArticleInline(admin.TabularInline):
    model = MarketWeekArticle
    extra = 0


class MarketDayEconomicInline(admin.TabularInline):
    model = MarketDayEconomic
    extra = 0


class MarketWeekEtfFlowInline(admin.TabularInline):
    model = MarketWeekEtfFlow
    extra = 0


class MarketWeekAdmin(OpinionAdmin):
    inlines = [
        MarketDayEconomicInline, MarketWeekResearchInline, MarketWeekArticleInline,

        MarketWeekCommitmentAdmin, MarketWeekRelocationInline,
        MarketWeekFundAdmin, MarketWeekFundNetCashAdmin,
        MarketWeekEtfFlowInline,

        MarketWeekSentimentAdmin, MarketWeekValuationAdmin,

        MarketWeekTechnicalAdmin,

        MarketWeekSectorAdmin, MarketWeekSectorItemAdmin,

        MarketWeekIndicesAdmin, MarketWeekCommodityAdmin,
        MarketWeekGlobalAdmin, MarketWeekCountryAdmin,
        MarketWeekImplVolAdmin,
    ]

    def link(self, obj):
        return '<a href="{link}">Link</a> | <a href="{report}">Report</a>'.format(
            link=reverse('market_week_create', kwargs={'obj_id': obj.id}),
            report=reverse('market_week_report', kwargs={'obj_id': obj.id}),
        )

    link.allow_tags = True
    link.short_description = ''

    list_display = (
        'date', 'link'
    )

    search_fields = ('date',)

    list_per_page = 20


class MarketStrategyOpportunityInline(admin.TabularInline):
    model = MarketStrategyOpportunity
    extra = 0


class MarketStrategyAllocationInline(admin.TabularInline):
    model = MarketStrategyAllocation
    extra = 0


class MarketStrategyDistributionInline(admin.TabularInline):
    model = MarketStrategyDistribution
    extra = 0


class MarketStrategyAdmin(OpinionAdmin):
    inlines = [
        MarketStrategyOpportunityInline,
        MarketStrategyAllocationInline,
        MarketStrategyDistributionInline
    ]

    def link(self, obj):
        return '<a href="{report}">Report</a>'.format(
            report=reverse('market_strategy_report', kwargs={'obj_id': obj.id}),
        )

    link.allow_tags = True
    link.short_description = ''

    list_display = (
        'date', 'economic', 'week_movement', 'link'
    )

    search_fields = ('date',)
    list_filter = ('economic', 'week_movement')

    list_per_page = 20


admin.site.register(MarketMonthEconomic, MarketMonthEconomicAdmin)
admin.site.register(MarketWeek, MarketWeekAdmin)
admin.site.register(MarketStrategy, MarketStrategyAdmin)
