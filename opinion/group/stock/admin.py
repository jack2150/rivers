from django.contrib import admin

from base.admin import DateForm
from opinion.group.stock.models import *
from opinion.group.report.admin import OpinionAdmin, OpinionStackedAdmin


class StockFundamentalInline(OpinionStackedAdmin):
    model = StockFundamental


class StockEarningInline(OpinionStackedAdmin):
    model = StockEarning


class StockOwnershipInline(OpinionStackedAdmin):
    model = StockOwnership


class StockInsiderInline(OpinionStackedAdmin):
    model = StockInsider


class StockIndustryInline(OpinionStackedAdmin):
    model = StockIndustry


class StockShortInterestInline(OpinionStackedAdmin):
    model = StockShortInterest


class StockProfileAdmin(OpinionAdmin):
    inlines = [
        StockFundamentalInline, StockIndustryInline,
        StockOwnershipInline, StockInsiderInline,
        StockShortInterestInline, StockEarningInline
    ]

    readonly_fields = ('report',)
    list_per_page = 20


class UnderlyingArticleAdmin(OpinionAdmin):
    list_display = (
        'report', 'category', 'name', 'rank', 'effect',
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
                'category', 'name', 'story', 'desc', 'period',
            )
        }),
        ('News summary', {
            'fields': (
                'rank', 'effect', 'good_news', 'bad_news'
            )
        }),
        ('News behavior', {
            'fields': (
                'fundamental_effect', 'rational', 'blind_follow', 'reversed',
            )
        }),
        ('Probability', {
            'fields': (
                'bull_chance', 'range_chance', 'bear_chance',
            )
        }),
    )
    search_fields = ('report__symbol', 'report__date', 'name')
    list_filter = ('category', 'story', 'period',
                   'rank', 'effect',)
    readonly_fields = ('report', )
    list_per_page = 20


admin.site.register(StockProfile, StockProfileAdmin)
admin.site.register(UnderlyingArticle, UnderlyingArticleAdmin)
