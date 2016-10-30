from django.contrib import admin
from views import *
from bootstrap3_datetime.widgets import DateTimePicker
from statement.position.views import *


class StartStopDateForm(forms.ModelForm):
    start = forms.DateField(widget=DateTimePicker(
        options={"format": "YYYY-MM-DD", "pickTime": False}))
    stop = forms.DateField(widget=DateTimePicker(
        options={"format": "YYYY-MM-DD", "pickTime": False}))


class StatementNameAdmin(admin.ModelAdmin):
    form = StartStopDateForm

    # noinspection PyMethodMayBeStatic
    def statement_import(self, obj):
        return '<a href="{link0}">Import</a> | <a href="{link1}">Truncate</a>'.format(
            link0=reverse('admin:statement_import', kwargs={'name_id': obj.id}),
            link1=reverse('admin:statement_truncate', kwargs={'name_id': obj.id}),
        )
    statement_import.allow_tags = True
    statement_import.short_description = ''

    list_display = (
        'name', 'short_name', 'path', 'cash_type', 'capital', 'start', 'stop', 'statement_import'
    )

    fieldsets = (
        ('Primary Fields', {
            'fields': (
                'name', 'short_name', 'path', 'cash_type', 'description', 'capital', 'start', 'stop'
            )
        }),
    )

    search_fields = ('name', 'short_name', 'description')
    list_filter = ('cash_type', )
    list_per_page = 20


class StatementForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}))


# noinspection PyMethodMayBeStatic
class StatementInline(admin.TabularInline):
    extra = 0
    ordering = ('time', )

    def date(self, obj):
        return obj.statement.date

    def has_add_permission(self, request):
        return False

    # def has_change_permission(self, request, obj=None):
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

    def name(self, obj):
        return obj.statement_name.name

    form = StatementForm

    inlines = (CashBalanceInline, AccountOrderInline, AccountTradeInline, HoldingEquityInline,
               HoldingOptionInline, ProfitLossInline)

    list_display = ('date', 'name', 'stock_bp', 'option_bp', 'commission_ytd',
                    'trades', 'positions', 'net_liquid', 'report')

    fieldsets = (
        ('Foreign Keys', {
            'fields': ('statement_name',)
        }),
        ('Primary Fields', {
            'fields': ('date', 'net_liquid', 'stock_bp', 'option_bp', 'commission_ytd', 'csv_data')
        })
    )

    search_fields = ('date', )
    list_filter = ('statement_name__name', )
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


# noinspection PyAbstractClass
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


class PositionAdmin(admin.ModelAdmin):
    form = StartStopDateForm
    inlines = (CashBalanceInline, AccountOrderInline, AccountTradeInline,
               HoldingEquityInline, HoldingOptionInline, ProfitLossInline)

    def link(self):
        return '<a href="{link0}">Report</a> | <a href="{link1}">Comment</a>'.format(
            link0=reverse('admin:position_report', kwargs={'id': self.id}),
            link1=reverse('admin:get_position_comment', kwargs={'position_id': self.id})
        )

    link.allow_tags = True
    link.short_description = ''

    list_display = ('symbol', 'statement', 'name', 'spread', 'status', 'start', 'stop', link)
    fieldsets = (
        ('Primary Fields', {
            'fields': ('statement', 'symbol', 'name', 'spread', 'status', 'start', 'stop')
        }),
    )

    search_fields = ('symbol', 'name', 'spread', 'status', 'start', 'stop')
    list_filter = ('statement__statement_name__short_name', 'status', 'name', 'spread')
    list_per_page = 20

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


class PositionCommentAdmin(admin.ModelAdmin):
    form = StatementForm
    list_display = ('position', 'date', 'strategy_test', 'target_price',
                    'market_review', 'complete_focus', 'mistake_trade')

    fieldsets = (
        ('Foreign Keys', {
            'fields': ('position',)
        }),
        ('Primary Fields', {
            'fields': ('date', 'description')
        }),
        ('Enter comment', {
            'fields': (
                'strategy_test', 'short_period', 'over_confidence', 'unknown_trade',
                'target_price', 'market_review', 'feel_lucky', 'wrong_timing',
                'well_backtest', 'valid_strategy', 'high_chance', 'chase_news',
                'deep_analysis', 'unaware_event', 'poor_estimate'
            )
        }),
        ('Holding comment', {
            'fields': (
                'keep_update', 'unaware_news', 'unaware_eco', 'unaware_stat',
                'hold_loser', 'wrong_wait', 'miss_profit', 'greed_wait'
            )
        }),
        ('Exit comment', {
            'fields': (
                'afraid_loss', 'luck_factor', 'news_effect', 'sold_early',
                'fear_factor', 'complete_focus', 'mistake_trade'
            )
        })
    )

    search_fields = ('position__name', 'position__spread', 'description')
    list_per_page = 20

    readonly_fields = ('position', )


#admin.site.app_index_template = 'statement/index.html'

# admin models
admin.site.register(StatementName, StatementNameAdmin)
admin.site.register(Statement, StatementAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(PositionStage, PositionStageAdmin)
admin.site.register(CashBalance, CashBalanceAdmin)
admin.site.register(AccountOrder, AccountOrderAdmin)
admin.site.register(AccountTrade, AccountTradeAdmin)
admin.site.register(HoldingEquity, HoldingEquityAdmin)
admin.site.register(HoldingOption, HoldingOptionAdmin)
admin.site.register(ProfitLoss, ProfitLossAdmin)
admin.site.register(PositionComment, PositionCommentAdmin)


# custom admin view
admin.site.register_view(
    'statement/import/(?P<name_id>\d+)/$', urlname='statement_import', view=statement_import
)

admin.site.register_view(
    'statement/position/spreads/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='position_spreads', view=position_spreads
)

admin.site.register_view(
    'statement/position/report/(?P<id>\d+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='position_report', view=position_report
)
admin.site.register_view(
    'statement/position/report/(?P<id>\d+)/$',
    urlname='position_report', view=position_report
)

admin.site.register_view(
    'statement/position/report2/(?P<pos_id>\d+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='position_report2', view=position_report2
)

admin.site.register_view(
    'statement/truncate/(?P<name_id>\d+)/$', urlname='statement_truncate', view=statement_truncate
)

admin.site.register_view(
    'data/underlying/daily/(?P<date>\d{4}-\d{2}-\d{2})/(?P<ready_all>\d+)/$',
    urlname='daily_import', view=daily_import
)

admin.site.register_view(
    'statement/position/comment/(?P<position_id>\d+)/$',
    urlname='get_position_comment', view=get_position_comment
)
