from django.contrib import admin
from django.core.urlresolvers import reverse
from base.admin import DateForm
from opinion.group.market.models import MarketMovement, MarketReview, MarketSentiment
from opinion.group.market.views import market_profile


class MarketMovementAdmin(admin.ModelAdmin):
    #

    list_display = (
        'date',
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
                'dow_phase', 'dow_movement', 'sector'
            )
        }),
        ('Commodity', {
            'fields': (
                'currency', 'bond', 'energy', 'metal', 'grain',
            )
        }),
        ('Economic Calendar', {
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


class MarketSentimentAdmin(admin.ModelAdmin):
    #

    def market_profile(self, obj):
        return '<a href="{link}">Profile</a>'.format(
            link=reverse('admin:market_profile', kwargs={'date': obj.date.strftime('%Y-%m-%d')})
        )

    market_profile.allow_tags = True
    market_profile.short_description = ''

    list_display = (
        'date', 'fund_cash_ratio', 'fear_greek_index', 'credit_balance', 'put_call_ratio',
        'investor_sentiment', 'futures_trader'
    )

    fieldsets = (
        ('Primary', {
            'fields': (
                'date',
            )
        }),
        ('Major Indicators', {
            'fields': (
                'fund_cash_ratio', 'fear_greek_index', 'margin_debt', 'credit_balance',
                'put_call_ratio', 'investor_sentiment', 'futures_trader', 'confidence_index',
                'ted_spread', 'market_breadth', 'ma200day_pct', 'arms_index',
            )
        })
    )

    search_fields = ('date',)
    list_per_page = 20


admin.site.register(MarketMovement, MarketMovementAdmin)
admin.site.register(MarketReview, MarketReviewAdmin)
admin.site.register(MarketSentiment, MarketSentimentAdmin)

admin.site.register_view(
    'opinion/profile/market/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='market_profile', view=market_profile
)
