from django.contrib import admin

from base.admin import DateForm
from opinion.stock.models import IndustryOpinion, FundamentalOpinion
from opinion.stock.views import industry_profile


class IndustryOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'symbol', 'date', 'industry', 'sector',
        'index_trend', 'isolate', 'risk_diff',
        'industry_pe', 'industry_rank', 'industry_fa', 'fair_value'
    )

    fieldsets = (
        ('Primary', {
            'fields': (
                'symbol', 'date', 'sector', 'industry'
            )
        }),
        ('Industry index', {
            'fields': (
                'index_trend', 'isolate', 'risk_diff'
            )
        }),
        ('Industry analysis', {
            'fields': (
                'biz_cycle', 'cs_trend', 'structural_chg', 'life_cycle', 'competition'
            )
        }),
        ('Industry valuation', {
            'fields': (
                'industry_pe', 'industry_rank', 'industry_fa', 'fair_value'
            )
        })
    )

    search_fields = ('symbol', 'date')
    list_filter = (
        'sector', 'index_trend', 'isolate', 'risk_diff',
        'industry_pe', 'industry_rank', 'industry_fa', 'fair_value'
    )
    list_per_page = 20


class FundamentalOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'symbol', 'date', 'ownership_activity', 'insider_trade', 'guru_trade', 'short_interest',
        'mean_rank', 'target_price_mean', 'earning_surprise', 'valuation',
    )
    fieldsets = (
        ('Primary', {
            'fields': (
                'symbol', 'date'
            )
        }),
        ('Ownership', {
            'fields': (
                'ownership_activity', 'insider_trade', 'guru_trade', 'short_interest',
            )
        }),
        ('Rank & Target Price', {
            'fields': (
                'mean_rank', 'target_price_max', 'target_price_mean', 'target_price_min',
            )
        }),
        ('Fundamental', {
            'fields': (
                'earning_surprise', 'earning_grow', 'dividend_grow',
                'dcf_value', 'pe_ratio_trend', 'div_yield_trend', 'valuation',
            )
        }),
    )

    search_fields = ('symbol', 'date')
    list_filter = (
        'ownership_activity', 'insider_trade', 'guru_trade', 'short_interest',
        'earning_surprise', 'earning_grow', 'dividend_grow',
        'pe_ratio_trend', 'div_yield_trend', 'valuation',

    )
    list_per_page = 20


admin.site.register(IndustryOpinion, IndustryOpinionAdmin)
admin.site.register(FundamentalOpinion, FundamentalOpinionAdmin)

admin.site.register_view(
    'opinion/profile/industry/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='industry_profile', view=industry_profile
)
