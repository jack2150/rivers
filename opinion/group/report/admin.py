from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db import models
from django.forms import Textarea

from opinion.group.stock.models import StockFundamental, StockIndustry, UnderlyingArticle
from opinion.group.report.models import UnderlyingReport


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


class UnderlyingReportAdmin(admin.ModelAdmin):
    # noinspection PyMethodMayBeStatic
    def report_link(self):
        links = [
            '<a href="{link}" target="_blank">Create report</a>'.format(
                link=reverse('underlying_report_create', kwargs={
                    'obj_id': self.id, 'process': "underlyingreport"
                })
            ),
            '<a href="{link}" target="_blank">Report summary</a>'.format(
                link=reverse('report_enter_summary', kwargs={'report_id': self.id})
            )
        ]

        return ' | '.join(links)

    report_link.allow_tags = True
    report_link.short_description = 'Action'

    list_display = (
        'date', 'symbol', 'asset', 'phase', 'close', report_link
    )
    fieldsets = (
        ('Primary', {'fields': ('date', 'symbol', 'asset', 'phase', 'close')}),
    )

    search_fields = (

    )
    list_filter = ()

    list_per_page = 20


admin.site.register(UnderlyingReport, UnderlyingReportAdmin)
