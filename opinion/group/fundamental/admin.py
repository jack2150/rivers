from django.contrib import admin

from base.admin import DateForm
from opinion.group.fundamental.models import StockIndustry, StockFundamental, UnderlyingArticle
from opinion.group.fundamental.views import industry_profile
from opinion.group.report.admin import OpinionAdmin


class StockIndustryAdmin(OpinionAdmin):
    list_display = (
        'report', 'direction', 'isolate', 'industry_rank', 'sector_rank',
        'stock_rank', 'stock_growth', 'stock_financial',
    )

    fieldsets = (
        ('Foreign key', {
            'fields': (
                'report',
            )
        }),
        ('Industry', {
            'fields': (
                'direction', 'isolate', 'industry_rank', 'sector_rank'
            )
        }),
        ('Valuation', {
            'fields': (
                'stock_rank', 'stock_growth', 'stock_financial',
            )
        })
    )

    search_fields = ('report__symbol', 'report__date')
    list_filter = (
        'direction', 'isolate', 'industry_rank', 'sector_rank',
        'stock_rank', 'stock_growth', 'stock_financial',
    )
    readonly_fields = ('report', )
    list_per_page = 20


class StockFundamentalAdmin(OpinionAdmin):
    list_display = (
        'report', 'mean_rank', 'accuracy', 'rank_change', 'change_date', 'risk',
        'ownership_activity', 'insider_trade', 'short_interest', 'risk'
    )
    fieldsets = (
        ('Foreign key', {
            'fields': (
                'report',
            )
        }),
        ('Ownership', {
            'fields': (
                'ownership_activity', 'ownership_date',
                'insider_trade', 'insider_date',
                'short_interest', 'short_date',
                'guru',
            )
        }),
        ('Rank & Target Price', {
            'fields': (
                'mean_rank', 'accuracy', 'rank_change', 'change_date', 'risk',
                'tp_max', 'tp_mean', 'tp_min'
            )
        })
    )

    search_fields = ('report__symbol', 'report__date')
    list_filter = (
        'ownership_activity', 'insider_trade', 'guru', 'short_interest',
    )
    readonly_fields = ('report', )
    list_per_page = 20


class UnderlyingArticleAdmin(admin.ModelAdmin):
    list_display = (
        'report', 'category', 'article_name', 'news_rank', 'news_effect',
        'bull_chance', 'range_chance', 'bear_chance',
    )
    fieldsets = (
        ('Foreign key', {
            'fields': (
                'report',
            )
        }),
        ('Primary news', {
            'fields': (
                'category', 'article_name', 'article_story', 'period_state',
            )
        }),
        ('News summary', {
            'fields': (
                'news_rank', 'news_effect',
            )
        }),
        ('News behavior', {
            'fields': (
                'fundamental_effect', 'rational', 'blind_follow', 'reverse_effect',
            )
        }),
        ('Probability', {
            'fields': (
                'bull_chance', 'range_chance', 'bear_chance',
            )
        }),
    )
    search_fields = ('report__symbol', 'report__date', 'article_name')
    list_filter = ('category', 'article_name', 'article_story', 'period_state',
                   'news_rank', 'news_effect',)
    readonly_fields = ('report', )
    list_per_page = 20


admin.site.register(StockIndustry, StockIndustryAdmin)
admin.site.register(StockFundamental, StockFundamentalAdmin)
admin.site.register(UnderlyingArticle, UnderlyingArticleAdmin)

admin.site.register_view(
    'opinion/profile/industry/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='industry_profile', view=industry_profile
)
