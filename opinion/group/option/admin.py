import logging
import pandas as pd
from django.contrib import admin
from django.core.urlresolvers import reverse

from opinion.group.option.models import *
from opinion.group.report.admin import OpinionAdmin
from rivers.settings import QUOTE_DIR

logger = logging.getLogger('views')


class OptionStatIVInline(admin.TabularInline):
    model = OptionStatIV


class OptionStatSizzleInline(admin.TabularInline):
    model = OptionStatSizzle


class OptionStatBidAskInline(admin.TabularInline):
    model = OptionStatBidAsk
    max_num = 3


class OptionStatOpenInterestInline(admin.TabularInline):
    model = OptionStatOpenInterest
    max_num = 3


class OptionStatTimeSaleContractInline(admin.TabularInline):
    model = OptionStatTimeSaleContract
    readonly_fields = [
        'option', 'ex_date', 'strike', 'name', 'qty', 'bid', 'ask', 'price', 'mark'
    ]
    can_delete = False
    exclude = ('option_stat',)
    max_num = 10

    def has_add_permission(self, request):
        return False


class OptionStatTimeSaleTradeInline(admin.TabularInline):
    model = OptionStatTimeSaleTrade
    readonly_fields = [
        'time', 'ex_date', 'strike', 'name', 'qty', 'bid', 'ask', 'price', 'mark',
        'trade', 'exchange', 'delta', 'iv', 'underlying_price', 'condition',
    ]
    fields = [
        'time', 'ex_date', 'strike', 'name', 'qty', 'bid', 'ask', 'price', 'mark',
        'trade', 'exchange', 'delta', 'iv', 'underlying_price', 'condition', 'fill'
    ]

    can_delete = False
    exclude = ('option_stat', 'option', )
    max_num = 10

    def has_add_permission(self, request):
        return False


class OptionStatAdmin(OpinionAdmin):
    inlines = [
        OptionStatIVInline,
        OptionStatSizzleInline,
        OptionStatBidAskInline,
        OptionStatOpenInterestInline,
        OptionStatTimeSaleContractInline,
        OptionStatTimeSaleTradeInline
    ]

    def timesale(self, obj):
        return '{link} | {report}'.format(
            link='<a href="%s" target="_blank">Create</a>' %
                 reverse('timesale_create', kwargs={'obj_id': obj.id}),
            report='<a href="%s" target="_blank"> Report</a>' %
                 reverse('timesale_report', kwargs={'obj_id': obj.id}),
        )

    timesale.allow_tags = True

    def action(self, obj):
        return '{report}'.format(
            report='<a href="%s" target="_blank"> Report</a>' %
                   reverse('report_option_stat', kwargs={'obj_id': obj.id}),
        )

    action.allow_tags = True

    list_display = (
        'symbol', 'date', 'timesale', 'action'
    )
    fieldsets = (
        ('Primary', {'fields': (
            'symbol', 'date'
        )}),
        ('Main chart', {'fields': (
            'iv_move_chart', 'stat_image',
        )}),
        ('Greek chart', {'fields': (
            'iv_term', 'iv_skew', 'iv_cycle_chart',
            'theta_skew', 'theta_chart',
            'vega_skew', 'vega_chart',
            'covered_chart', 'interest_chart', 'volume_chart'
        )}),
        ('Timesale', {'fields': (
            'raw_data',
        )}),
    )

    search_fields = ('symbol', )
    list_per_page = 20


admin.site.register(OptionStat, OptionStatAdmin)
# admin.site.register(OptionStatTimeSale, OptionTimeSaleAdmin)
