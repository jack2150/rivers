from django.contrib import admin
from django.core.urlresolvers import reverse
from base.admin import DateForm
from opinion.market.models import MarketMovement, MarketValuation, MarketIndicator
from opinion.market.views import market_profile


class MarketMovementAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'date', 'current_long_trend', 'current_short_trend', 'volatility',
        'market_indicator', 'extra_attention', 'key_indicator', 'special_news'
    )

    fieldsets = (
        ('Primary', {
            'fields': (
                'date',
            )
        }),
        ('Stock Market', {
            'fields': (
                'previous_short_trend', 'current_short_trend',
                'previous_long_trend', 'current_long_trend'
            )
        }),
        ('Major Market', {
            'fields': (
                'volatility', 'bond', 'commodity', 'currency',
            )
        }),
        ('Economic Calendar', {
            'fields': (
                'market_indicator', 'extra_attention', 'key_indicator', 'special_news'
            )
        }),
        ('Others', {
            'fields': (
                'commentary',
            )
        })
    )

    search_fields = ('date',)
    list_per_page = 20


class MarketValuationAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'date', 'cli_trend', 'bci_trend', 'market_scenario', 'money_supply'
    )

    fieldsets = (
        ('Primary', {
            'fields': (
                'date',
            )
        }),
        ('Major Economic', {
            'fields': (
                'cli_trend', 'bci_trend', 'market_scenario', 'money_supply'
            )
        }),
        ('Monetary Policy', {
            'fields': (
                'monetary_policy',
            )
        }),
    )

    search_fields = ('date', 'cli_trend', 'bci_trend', 'market_scenario', 'money_supply')
    list_per_page = 20


class MarketIndicatorAdmin(admin.ModelAdmin):
    form = DateForm

    def market_profile(self, obj):
        return '<a href="{link}">Profile</a>'.format(
            link=reverse('admin:market_profile', kwargs={'date': obj.date.strftime('%Y-%m-%d')})
        )

    market_profile.allow_tags = True
    market_profile.short_description = ''

    list_display = (
        'date', 'fund_cash_ratio', 'fear_greek_index', 'credit_balance', 'put_call_ratio',
        'investor_sentiment', 'futures_trader', 'support_price', 'resistant_price', 'market_profile'
    )

    fieldsets = (
        ('Primary', {
            'fields': (
                'date',
            )
        }),
        ('Major Indicators', {
            'fields': (
                'fund_cash_ratio', 'fear_greek_index', 'credit_balance', 'put_call_ratio',
                'investor_sentiment', 'futures_trader', 'confidence_index', 'ted_spread',
                'margin_debt', 'market_breadth', 'ma200day_pct', 'arms_index',
            )
        }),
        ('Market Price Range', {
            'fields': (
                'support_price', 'resistant_price',
            )
        }),
        ('Dow theory', {
            'fields': (
                'dow_phase', 'dow_movement', 'dow_ma200x50', 'dow_volume'
            )
        }),
        ('Others technical/valuation', {
            'fields': (
                'ma50_confirm', 'fair_value_trend'
            )
        })
    )

    search_fields = ('date',)
    list_per_page = 20


admin.site.register(MarketMovement, MarketMovementAdmin)
admin.site.register(MarketValuation, MarketValuationAdmin)
admin.site.register(MarketIndicator, MarketIndicatorAdmin)

admin.site.register_view(
    'opinion/profile/market/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='market_profile', view=market_profile
)