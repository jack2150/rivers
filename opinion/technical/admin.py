from django.contrib import admin

from base.admin import DateForm
from opinion.technical.models import TechnicalOpinion, TechnicalRank


class TechnicalRankAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'symbol', 'date', 'market_edge', 'the_street', 'ford_equity', 'bar_chart', 'sctr_rank'
    )
    fieldsets = (
        ('Primary', {
            'fields': ('symbol', 'date')
        }),
        ('Ranking Provider', {
            'fields': ('market_edge', 'the_street', 'ford_equity', 'bar_chart', 'sctr_rank')
        }),
    )

    search_fields = ('symbol', 'date',)
    list_filter = ()
    list_per_page = 20


class TechnicalOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'symbol', 'date',
        'sma50_trend', 'sma200_trend', 'sma_cross', 'rsi_score',
        'volume_profile', 'vwap_average', 'acc_dist',
        'extra_analysis'
    )
    fieldsets = (
        ('Primary', {
            'fields': ('symbol', 'date')
        }),
        ('Basic Technical Analysis', {
            'fields': ('sma50_trend', 'sma200_trend', 'sma_cross', 'rsi_score')
        }),
        ('Volume Base Analysis', {
            'fields': ('volume_profile', 'vwap_average', 'acc_dist')
        }),
        ('Ichimoku Cloud', {
            'fields': ('ichimoku_cloud', 'ichimoku_color', 'ichimoku_base', 'ichimoku_conversion')
        }),
        ('Parabolic & DMI', {
            'fields': ('parabolic_trend', 'parabolic_cross', 'dmi_trend', 'dmi_cross')
        }),
        ('Stochastic', {
            'fields': ('stoch_score0', 'stoch_score1', 'stoch_score2')
        }),
        ('Bollinger Band & MACD', {
            'fields': ('band_score', 'macd_score',)
        }),
        ('Extra & Description', {
            'fields': ('extra_analysis', 'description')
        }),
    )

    search_fields = ('symbol', 'date',)
    list_filter = (
        'sma50_trend', 'sma200_trend', 'sma_cross', 'rsi_score',
        'volume_profile', 'vwap_average', 'acc_dist',
        'ichimoku_cloud', 'ichimoku_color', 'ichimoku_base', 'ichimoku_conversion',
        'parabolic_trend', 'parabolic_cross', 'dmi_trend', 'dmi_cross',
        'stoch_score0', 'stoch_score1', 'stoch_score2',
        'band_score', 'macd_score',
    )
    list_per_page = 20


admin.site.register(TechnicalRank, TechnicalRankAdmin)
admin.site.register(TechnicalOpinion, TechnicalOpinionAdmin)
