from django.contrib import admin

from base.admin import DateForm
from opinion.group.technical.models import TechnicalOpinion, TechnicalRank


class TechnicalRankAdmin(admin.ModelAdmin):


    list_display = (
        'symbol', 'date', 'market_edge', 'bar_chart', 'chartmill'
    )
    fieldsets = (
        ('Primary', {
            'fields': ('symbol', 'date')
        }),
        ('Rank Provider', {
            'fields': ('market_edge', 'bar_chart', 'chartmill')
        }),
    )

    search_fields = ('symbol', 'date',)
    list_filter = ('market_edge', 'bar_chart', 'chartmill')
    list_per_page = 20


class TechnicalOpinionAdmin(admin.ModelAdmin):


    list_display = (
        'symbol', 'date',
        'sma50_trend', 'sma200_trend', 'sma_cross', 'rsi_score',
        'volume_profile', 'vwap_average', 'acc_dist',
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
            'fields': ('ichimoku_cloud', 'ichimoku_color', 'ichimoku_base', 'ichimoku_convert')
        }),
        ('Parabolic & DMI', {
            'fields': ('parabolic_trend', 'parabolic_cross', 'dmi_trend', 'dmi_cross')
        }),
        ('Stochastic', {
            'fields': ('stoch_fast', 'stoch_full')
        }),
        ('Bollinger Band & MACD', {
            'fields': ('band_score', 'macd_score')
        }),
        ('FW Mobo & MMG', {
            'fields': ('fw_mobo_trend', 'fw_mobo_signal', 'fw_mmg_signal', 'fw_mmg_trend')
        }),
        ('Pivot & 4% & TrendNoise', {
            'fields': ('pivot_point', 'four_percent', 'trend_noise')
        }),
        ('TPO & Freedom movement', {
            'fields': ('tpo_profile', 'free_move', 'relative_vol', 'market_forecast')
        }),
        ('TTM', {
            'fields': ('ttm_trend', 'ttm_alert', 'ttm_linear', 'ttm_squeeze', 'ttm_wave')
        }),
        ('ZigZag', {
            'fields': ('zigzag_pct', 'zigzag_sign')
        }),
        ('Aroon', {
            'fields': ('aroon_ind', 'aroon_osc')
        }),

        ('Detail explain', {
            'fields': ('description', )
        }),
    )

    search_fields = ('symbol', 'date',)
    list_filter = ('sma50_trend', 'sma200_trend', 'sma_cross',
                   'volume_profile', 'vwap_average', 'acc_dist')
    list_per_page = 20


admin.site.register(TechnicalRank, TechnicalRankAdmin)
admin.site.register(TechnicalOpinion, TechnicalOpinionAdmin)
