from django.contrib import admin

from base.admin import DateForm
from opinion.group.fundamental.models import StockIndustry, StockFundamental, UnderlyingArticle
from opinion.group.fundamental.views import industry_profile


class StockIndustryAdmin(admin.ModelAdmin):


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


class StockFundamentalAdmin(admin.ModelAdmin):


    list_display = (
        'symbol', 'date', 'ownership_activity', 'insider_trade',
        'guru_trade', 'short_interest', 'risk'
    )
    fieldsets = (
        ('Primary', {
            'fields': (
                'symbol', 'date'
            )
        }),
        ('Ownership', {
            'fields': (
                'ownership_activity', 'insider_trade', 'guru_trade', 'short_interest', 'risk'
            )
        }),
        ('Rank & Target Price', {
            'fields': (
                'mean_rank', 'target_price_max', 'target_price_mean', 'target_price_min',
            )
        }),
    )

    search_fields = ('symbol', 'date')
    list_filter = (
        'ownership_activity', 'insider_trade', 'guru_trade', 'short_interest',

    )
    list_per_page = 20


class UnderlyingArticleAdmin(admin.ModelAdmin):


    list_display = (
        'symbol', 'date', 'category', 'article_name', 'bull_chance', 'range_chance', 'bear_chance',
    )
    fieldsets = (
        ('Primary', {
            'fields': (
                'symbol', 'date',
            )
        }),
        ('Analysis', {
            'fields': (
                'category', 'article_name',
                'article_story', 'period_state', 'fundamental_effect',
                'rational', 'blind_follow', 'reverse_effect',
                'bull_chance', 'range_chance', 'bear_chance',
            )
        })
    )
    search_fields = ('date', 'article_name')
    list_filter = ('category', 'article_name',
                   'article_story', 'period_state', 'fundamental_effect',
                   'rational', 'blind_follow', 'reverse_effect')
    list_per_page = 20


admin.site.register(StockIndustry, StockIndustryAdmin)
admin.site.register(StockFundamental, StockFundamentalAdmin)
admin.site.register(UnderlyingArticle, UnderlyingArticleAdmin)

admin.site.register_view(
    'opinion/profile/industry/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='industry_profile', view=industry_profile
)
