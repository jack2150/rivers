from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db import models
from django.forms import Textarea

from opinion.group.stock.models import StockFundamental, StockIndustry, UnderlyingArticle
from opinion.group.report.models import ReportEnter, SubtoolOpinion


class OpinionAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 60})},
    }


class OpinionStackedAdmin(admin.StackedInline):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 60})},
    }


class StockFundamentalInline(admin.TabularInline):
    model = StockFundamental
    extra = 1


class StockIndustryInline(admin.TabularInline):
    model = StockIndustry
    extra = 1


class UnderlyingArticleInline(admin.TabularInline):
    model = UnderlyingArticle
    extra = 1


class SubtoolOpinionInline(admin.TabularInline):
    model = SubtoolOpinion
    extra = 3


class ReportEnterAdmin(admin.ModelAdmin):
    inlines = (SubtoolOpinionInline, )

    # noinspection PyMethodMayBeStatic
    def report_link(self):
        links = [
            '<a href="{link}" target="_blank">Create report</a>'.format(
                link=reverse('report_enter_create', kwargs={'symbol': self.symbol, 'date': self.date})
            ),
            '<a href="{link}" target="_blank">Report summary</a>'.format(
                link=reverse('report_enter_summary', kwargs={'report_id': self.id})
            )
        ]

        return ' | '.join(links)

    report_link.allow_tags = True
    report_link.short_description = 'Action'

    list_display = (
        'date', 'symbol', 'close', report_link
    )
    fieldsets = (
        ('Primary', {'fields': ('date', 'symbol', 'close')}),
    )

    search_fields = (

    )
    list_filter = ()

    list_per_page = 20


admin.site.register(ReportEnter, ReportEnterAdmin)
