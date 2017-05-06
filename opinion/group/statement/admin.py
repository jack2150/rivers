from django.contrib import admin
from django.core.urlresolvers import reverse
from opinion.group.report.admin import OpinionStackedAdmin, OpinionAdmin
from opinion.group.statement.models import *


class IBMonthNavInline(OpinionStackedAdmin):
    model = IBMonthNav


class IBMonthMarkInline(OpinionStackedAdmin):
    model = IBMonthMark


class IBMonthTradeFeeInline(OpinionStackedAdmin):
    model = IBMonthTradeFee


class IBMonthTradeOrderInline(OpinionStackedAdmin):
    model = IBMonthTradeOrder


class IBMonthTradeOtherInline(OpinionStackedAdmin):
    model = IBMonthTradeOther


class IBMonthTradeExchangeInline(admin.TabularInline):
    model = IBMonthTradeExchange
    extra = 0


class IBMonthTradeReturnInline(OpinionStackedAdmin):
    model = IBMonthTradeReturn


class IBMonthTradeDTEInline(OpinionStackedAdmin):
    model = IBMonthTradeDTE


class IBMonthXrayNoteInline(OpinionStackedAdmin):
    model = IBMonthXrayNote
    extra = 0


class IBMonthXRayGlobalInline(OpinionStackedAdmin):
    model = IBMonthXrayGlobal


class IBMonthXRaySectorInline(admin.TabularInline):
    model = IBMonthXraySector
    extra = 0


class IBMonthXRayStockStyleInline(admin.TabularInline):
    model = IBMonthXrayStockStyle
    extra = 0


class IBMonthXRayStockTypeInline(admin.TabularInline):
    model = IBMonthXrayStockType
    extra = 0


class IBMonthStatementAdmin(OpinionAdmin):
    inlines = [
        IBMonthNavInline, IBMonthMarkInline,
        IBMonthTradeFeeInline, IBMonthTradeOrderInline,
        IBMonthTradeReturnInline,
        IBMonthTradeExchangeInline, IBMonthTradeOtherInline,
        IBMonthTradeDTEInline,

        IBMonthXrayNoteInline, IBMonthXRayGlobalInline,
        IBMonthXRaySectorInline, IBMonthXRayStockStyleInline, IBMonthXRayStockTypeInline
    ]

    def link(self, obj):
        return '<a href="{report}">Report</a>'.format(
            report=reverse('ib_month_statement_report', kwargs={'obj_id': obj.id}),
        )

    link.allow_tags = True
    link.short_description = ''

    list_display = (
        'date', 'ibmonthnav', 'ibmonthmark', 'ibmonthtradefee', 'link'
    )

    fieldsets = (
        ('Primary', {
            'fields': ('date',)
        }),
    )

    search_fields = ('date',)

    list_per_page = 20


admin.site.register(IBMonthStatement, IBMonthStatementAdmin)
