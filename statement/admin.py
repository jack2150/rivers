from django.contrib import admin
from views import *
from bootstrap3_datetime.widgets import DateTimePicker
from statement.position.views import *


class StatementForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD",
                                       "pickTime": False}))


# noinspection PyMethodMayBeStatic
class StatementInline(admin.TabularInline):
    extra = 0
    ordering = ('time', )

    def date(self, obj):
        return obj.statement.date

    def has_add_permission(self, request):
        return False

    #def has_change_permission(self, request, obj=None):
    #    return False

    def has_delete_permission(self, request, obj=None):
        return False


class CashBalanceInline(StatementInline):
    model = CashBalance

    fields = ('date', 'time', 'name', 'ref_no', 'description',
              'fee', 'commission', 'amount', 'balance')
    readonly_fields = ('date', 'time', 'name', 'ref_no', 'description',
                       'fee', 'commission', 'amount', 'balance')


class AccountOrderInline(StatementInline):
    model = AccountOrder

    fields = ('date', 'time', 'spread', 'side', 'qty', 'pos_effect', 'symbol',
              'exp', 'strike', 'contract', 'price', 'order', 'tif', 'status')

    readonly_fields = ('date', 'time', 'spread', 'side', 'qty', 'pos_effect', 'symbol',
                       'exp', 'strike', 'contract', 'price', 'order', 'tif', 'status')


class AccountTradeInline(StatementInline):
    model = AccountTrade

    fields = ('date', 'time', 'spread', 'side', 'qty', 'pos_effect', 'symbol', 'exp',
              'strike', 'contract', 'price', 'net_price', 'order_type')

    readonly_fields = ('date', 'time', 'spread', 'side', 'qty', 'pos_effect', 'symbol', 'exp',
                       'strike', 'contract', 'price', 'net_price', 'order_type')


class HoldingEquityInline(StatementInline):
    model = HoldingEquity

    fields = ('date', 'symbol', 'description', 'qty', 'trade_price', 'close_price', 'close_value')

    readonly_fields = ('date', 'symbol', 'description', 'qty', 'trade_price', 'close_price', 'close_value')

    ordering = ('symbol', )


class HoldingOptionInline(StatementInline):
    model = HoldingOption

    fields = ('date', 'symbol', 'option_code', 'exp', 'strike', 'contract',
              'qty', 'trade_price', 'close_price', 'close_value')

    readonly_fields = ('date', 'symbol', 'option_code', 'exp', 'strike', 'contract',
                       'qty', 'trade_price', 'close_price', 'close_value')

    ordering = ('symbol', )


class ProfitLossInline(StatementInline):
    model = ProfitLoss

    fields = ('date', 'symbol', 'description', 'pl_open', 'pl_pct',
              'pl_day', 'pl_ytd', 'margin_req', 'close_value')

    readonly_fields = ('date', 'symbol', 'description', 'pl_open', 'pl_pct',
                       'pl_day', 'pl_ytd', 'margin_req', 'close_value')

    ordering = ('symbol', )


# noinspection PyMethodMayBeStatic
class StatementAdmin(admin.ModelAdmin):
    def report(self, obj):
        return '<a href="{link}">Spread</a>'.format(
            link=reverse('admin:position_spreads', kwargs={'date': obj.date})
        )

    report.allow_tags = True
    report.short_description = ''

    def positions(self, obj):
        return obj.profitloss_set.count()

    def trades(self, obj):
        return len(obj.accounttrade_set.distinct('symbol'))

    form = StatementForm

    inlines = (CashBalanceInline, AccountOrderInline, AccountTradeInline, HoldingEquityInline,
               HoldingOptionInline, ProfitLossInline)

    list_display = ('date',  'stock_bp', 'option_bp', 'commission_ytd',
                    'trades', 'positions', 'net_liquid', 'report')

    fieldsets = (
        ('Primary Fields', {
            'fields': ('date', 'net_liquid', 'stock_bp', 'option_bp', 'commission_ytd', 'csv_data')
        }),
    )

    search_fields = ('date', )
    list_per_page = 20

    def has_add_permission(self, request):
        return False


# noinspection PyMethodMayBeStatic
class StatementModelAdmin(admin.ModelAdmin):
    def date(self, obj):
        return obj.statement.date

    date.short_description = 'Date'
    date.admin_order_field = 'statement__date'

    def has_add_permission(self, request):
        return False


class CashBalanceAdmin(StatementModelAdmin):
    form = StatementForm  # enable bootstrap datetime js

    list_display = ['date', 'time', 'name', 'ref_no', 'description',
                    'fee', 'commission', 'amount', 'balance']

    fieldsets = (
        ('Foreign Keys', {
            'fields': (
                'statement', 'position'
            )
        }),
        ('Primary Fields', {
            'fields': (
                'time', 'name', 'ref_no', 'description',
                'fee', 'commission', 'amount', 'balance'
            )
        }),
    )

    search_fields = ('statement__date', 'name', 'ref_no', 'description')
    list_filter = ('name', )

    list_per_page = 20


class SpreadFilter(admin.SimpleListFilter):
    """
    Remove re, oco, trg spread
    """
    title = ('Spread', )
    parameter_name = 'spread'

    def lookups(self, request, model_admin):
        spreads = set([(ao.spread, ao.spread) for ao in model_admin.model.objects.all()])
        return [(s[0], s[1]) for s in spreads if '#' not in s[0]]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(spread=self.value())
        else:
            return queryset


class AccountOrderAdmin(StatementModelAdmin):
    form = StatementForm  # enable bootstrap datetime js

    list_display = [
        'date', 'time', 'spread', 'side', 'qty', 'pos_effect', 'symbol',
        'exp', 'strike', 'contract', 'price', 'order', 'tif', 'status'
    ]

    fieldsets = (
        ('Foreign Keys', {
            'fields': (
                'statement', 'position'
            )
        }),
        ('Primary Fields', {
            'fields': (
                'time', 'spread', 'side', 'qty', 'pos_effect', 'symbol', 'exp',
                'strike', 'contract', 'price', 'order', 'tif', 'status'
            )
        }),
    )

    search_fields = ('statement__date', 'time', 'spread', 'pos_effect', 'symbol', 'exp',
                     'strike', 'contract', 'price', 'order', 'tif', 'status')

    list_filter = (SpreadFilter, 'pos_effect', 'contract', 'order', 'tif')

    list_per_page = 20


class AccountTradeAdmin(StatementModelAdmin):
    form = StatementForm  # enable bootstrap datetime js

    list_display = [
        'date', 'time', 'spread', 'side', 'qty', 'pos_effect', 'symbol', 'exp',
        'strike', 'contract', 'price', 'net_price', 'order_type'
    ]

    fieldsets = (
        ('Foreign Keys', {
            'fields': (
                'statement', 'position'
            )
        }),
        ('Primary Fields', {
            'fields': (
                'time', 'spread', 'side', 'qty', 'pos_effect', 'symbol', 'exp',
                'strike', 'contract', 'price', 'net_price', 'order_type'
            )
        }),
    )

    search_fields = ('statement__date', 'time', 'spread', 'side', 'qty', 'pos_effect',
                     'symbol', 'exp', 'strike', 'contract', 'price', 'net_price', 'order_type')

    list_filter = ('spread', 'side', 'pos_effect', 'contract', 'order_type')

    list_per_page = 20


class HoldingEquityAdmin(StatementModelAdmin):
    form = StatementForm  # enable bootstrap datetime js

    list_display = [
        'date', 'symbol', 'description', 'qty', 'trade_price', 'close_price', 'close_value'
    ]

    fieldsets = (
        ('Foreign Keys', {
            'fields': (
                'statement', 'position'
            )
        }),
        ('Primary Fields', {
            'fields': (
                'symbol', 'description', 'qty', 'trade_price', 'close_price', 'close_value'
            )
        }),
    )

    search_fields = ('statement__date', 'symbol', 'description')

    list_per_page = 20


class HoldingOptionAdmin(StatementModelAdmin):
    form = StatementForm  # enable bootstrap datetime js

    list_display = [
        'date', 'symbol', 'option_code', 'exp', 'strike', 'contract',
        'qty', 'trade_price', 'close_price', 'close_value'
    ]

    fieldsets = (
        ('Foreign Keys', {
            'fields': (
                'statement', 'position'
            )
        }),
        ('Primary Fields', {
            'fields': (
                'symbol', 'option_code', 'exp', 'strike', 'contract',
                'qty', 'trade_price', 'close_price', 'close_value'
            )
        }),
    )

    search_fields = ('symbol', 'option_code')
    list_filter = ('contract', )

    list_per_page = 20


class ProfitLossAdmin(StatementModelAdmin):
    list_display = [
        'date', 'symbol', 'description', 'pl_open', 'pl_pct',
        'pl_day', 'pl_ytd', 'margin_req', 'close_value'
    ]

    fieldsets = (
        ('Foreign Keys', {
            'fields': (
                'statement', 'position'
            )
        }),
        ('Primary Fields', {
            'fields': (
                'symbol', 'description', 'pl_open', 'pl_pct',
                'pl_day', 'pl_ytd', 'margin_req', 'close_value',
            )
        }),
    )

    search_fields = ('symbol', 'description', 'statement__date')

    list_per_page = 20


class PositionForm(forms.ModelForm):
    start = forms.DateField(widget=DateTimePicker(
        options={"format": "YYYY-MM-DD", "pickTime": False}))
    stop = forms.DateField(widget=DateTimePicker(
        options={"format": "YYYY-MM-DD", "pickTime": False}))


class HoldingOpinionInline(StatementInline):
    model = HoldingOpinion
    fields = ('condition', 'action', 'opinion', 'news_level', 'news_effect', 'check_all', 'special')
    readonly_fields = ('condition', 'action', 'opinion', 'news_level',
                       'news_effect', 'check_all', 'special')
    ordering = ('date', )


class ExitOpinionInline(StatementInline):
    model = ExitOpinion
    fields = ('auto_trigger', 'condition', 'result', 'amount', 'price', 'timing', 'wait')
    readonly_fields = ('auto_trigger', 'condition', 'result', 'amount', 'price', 'timing', 'wait')
    ordering = ('date', )


class PositionAdmin(admin.ModelAdmin):
    form = PositionForm
    inlines = (CashBalanceInline, AccountOrderInline, AccountTradeInline,
               HoldingEquityInline, HoldingOptionInline, ProfitLossInline,
               HoldingOpinionInline, ExitOpinionInline)

    def report(self):
        return '<a href="{link}">Report</a>'.format(
            link=reverse('admin:position_report', kwargs={'id': self.id})
        )

    report.allow_tags = True
    report.short_description = ''

    list_display = ('symbol', 'name', 'spread', 'status', 'start', 'stop', report)

    search_fields = ('symbol', 'name', 'spread', 'status', 'start', 'stop')
    list_per_page = 20

    fieldsets = (
        ('Primary Fields', {
            'fields': ('symbol', 'name', 'spread', 'status', 'start', 'stop')
        }),
        ('Foreign Fields', {
            'fields': ('market_opinion', 'enter_opinion', 'strategy_result')
        })
    )

    def has_add_permission(self, request):
        return False


class PositionStageAdmin(admin.ModelAdmin):
    list_display = ('position', 'price', 'lt_stage', 'lt_amount',
                    'e_stage', 'e_amount', 'gt_stage', 'gt_amount')

    search_fields = ('position__symbol', 'position__name', 'position__spread', 'position__status',
                     'price', 'lt_stage', 'lt_amount', 'e_stage', 'e_amount', 'gt_stage', 'gt_amount')
    list_per_page = 20

    fieldsets = (
        ('Foreign Keys', {
            'fields': ('position', )
        }),
        ('Primary Fields', {
            'fields': ('price', 'lt_stage', 'lt_amount',
                       'e_stage', 'e_amount', 'gt_stage', 'gt_amount')
        }),
    )

    def has_add_permission(self, request):
        return False


#admin.site.app_index_template = 'statement/index.html'
# admin models
admin.site.register(Statement, StatementAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(PositionStage, PositionStageAdmin)
admin.site.register(CashBalance, CashBalanceAdmin)
admin.site.register(AccountOrder, AccountOrderAdmin)
admin.site.register(AccountTrade, AccountTradeAdmin)
admin.site.register(HoldingEquity, HoldingEquityAdmin)
admin.site.register(HoldingOption, HoldingOptionAdmin)
admin.site.register(ProfitLoss, ProfitLossAdmin)

# custom admin view
admin.site.register_view(
    'statement/import',
    urlname='statement_import',
    view=statement_import
)

admin.site.register_view(
    'statement/position/spreads/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='position_spreads',
    view=position_spreads
)

admin.site.register_view(
    'checklist/create/(?P<opinion>\w{4})/(?P<id>\d+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='create_opinion',
    view=create_opinion
)

admin.site.register_view(
    'statement/position/blind_strategy/(?P<id>\d+)/$',
    urlname='blind_strategy',
    view=blind_strategy
)

admin.site.register_view(
    'statement/position/report/(?P<id>\d+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='position_report',
    view=position_report
)
admin.site.register_view(
    'statement/position/report/(?P<id>\d+)/$',
    urlname='position_report',
    view=position_report
)

admin.site.register_view(
    'statement/truncate/$', urlname='truncate_statement', view=truncate_statement
)
