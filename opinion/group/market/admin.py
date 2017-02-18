from django.contrib import admin
from django.core.urlresolvers import reverse
from opinion.group.market.models import *
from opinion.group.market.views import market_profile
from opinion.group.report.admin import OpinionStackedAdmin


class CommodityMovementInline(admin.TabularInline):
    model = CommodityMovement
    extra = 0


class WorldMovementInline(admin.TabularInline):
    model = WorldMovement
    extra = 0


class SectorMovementInline(admin.TabularInline):
    model = SectorMovement
    extra = 0


class MarketMovementAdmin(admin.ModelAdmin):
    inlines = [CommodityMovementInline, SectorMovementInline, WorldMovementInline]

    list_display = (
        'date', 'resistant', 'resistant', 'volume', 'vix', 'technical_rank',
        'market_indicator', 'extra_attention', 'key_indicator', 'special_news'
    )

    fieldsets = (
        ('Primary', {
            'fields': (
                'date',
            )
        }),
        ('Indices', {
            'fields': (
                'resistant', 'resistant', 'volume', 'vix', 'technical_rank',
                'dow_phase', 'dow_movement'
            )
        }),
        ('Eco Data', {
            'fields': (
                'market_indicator', 'extra_attention', 'key_indicator', 'special_news'
            )
        })
    )

    search_fields = ('date',)
    list_per_page = 20


class MarketReviewAdmin(admin.ModelAdmin):
    #

    list_display = ('date', 'bubble_stage', 'market_scenario', 'cli_trend', 'bci_trend')

    fieldsets = (
        ('Primary', {
            'fields': ('date',)
        }),
        ('Major economics', {
            'fields': (
                'bubble_stage', 'market_scenario', 'cli_trend', 'bci_trend'
            )
        }),
        ('Economics data', {
            'fields': (
                'm2_supply', 'gdp', 'cpi', 'ppi', 'cc_survey',
                'employ', 'retail_sale', 'house_start', 'industry', 'biz_inventory',
                'startup', 'week_earning', 'currency_strength', 'interest_rate',
                'corp_profit', 'trade_deficit'
            )
        }),
        ('Commentary', {
            'fields': (
                'monetary_policy', 'month_commentary'
            )
        }),
    )

    search_fields = ('date', )
    list_per_page = 20


class MarketWeekTechnicalAdmin(OpinionStackedAdmin):
    model = MarketWeekTechnical


class MarketWeekReportAdmin(OpinionStackedAdmin):
    model = MarketWeekReport
    extra = 0


class MarketSentimentAdmin(admin.ModelAdmin):
    inlines = [MarketWeekTechnicalAdmin, MarketWeekReportAdmin]

    def market_profile(self, obj):
        return '<a href="{link}">Profile</a>'.format(
            link=reverse('admin:market_profile', kwargs={'date': obj.date.strftime('%Y-%m-%d')})
        )

    market_profile.allow_tags = True
    market_profile.short_description = ''

    list_display = (
        'date', 'fund_cash_ratio', 'sentiment_index', 'credit_balance', 'put_call_ratio',
        'investor_sentiment', 'futures_trader'
    )

    fieldsets = (
        ('Primary', {
            'fields': (
                'date',
            )
        }),
        ('Fund cash flow', {
            'fields': (
                'fund_cash_ratio', 'margin_debt', 'credit_balance', 'confidence_index',
                'futures_trader',
            )
        }),
        ('Sentiment indicator', {
            'fields': (
                'sentiment_index', 'put_call_ratio',
                'market_momentum', 'junk_bond_demand', 'price_strength',
                'safe_heaven_demand', 'market_volatility'
            )
        }),
        ('Third party', {
            'fields': (
                'investor_sentiment', 'ted_spread', 'market_breadth',
                'ma200day_pct', 'arms_index',
            )
        }),
    )

    search_fields = ('date',)
    list_per_page = 20


class MarketArticleAdmin(admin.ModelAdmin):
    # noinspection PyMethodMayBeStatic
    def source_url(self, obj):
        return '<a href="{link}" target="_blank">Read</a>'.format(link=obj.link)

    source_url.allow_tags = True
    source_url.short_description = ''

    list_display = (
        'date', 'name', 'category', 'chance', 'source_url'
    )

    fieldsets = (
        ('Primary', {
            'fields': (
                'date', 'link', 'name', 'category', 'chance',
            )
        }),
        ('Article', {
            'fields': (
                'key_point',
            )
        })
    )

    search_fields = ('date', 'link', 'name', 'key_point')
    list_filter = ('category', 'chance')
    list_per_page = 20


admin.site.register(MarketMovement, MarketMovementAdmin)
admin.site.register(MarketReview, MarketReviewAdmin)
admin.site.register(MarketSentiment, MarketSentimentAdmin)
admin.site.register(MarketArticle, MarketArticleAdmin)

admin.site.register_view(
    'opinion/profile/market/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='market_profile', view=market_profile
)
