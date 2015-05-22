from django.contrib import admin
from django import forms
from views import *
from models import *
from bootstrap3_datetime.widgets import DateTimePicker


class StatementForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD",
                                       "pickTime": False}))


class StatementInline(admin.TabularInline):
    extra = 0
    ordering = ('time', )

    def date(self, obj):
        return obj.statement.date

    def has_add_permission(self, request):
        return False

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


class StatementAdmin(admin.ModelAdmin):
    form = StatementForm

    inlines = (CashBalanceInline, AccountOrderInline, AccountTradeInline, HoldingEquityInline,
               HoldingOptionInline, ProfitLossInline)

    list_display = ('date', 'net_liquid', 'stock_bp', 'option_bp', 'commission_ytd')

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

    list_display = [
        'date', 'time', 'name', 'ref_no', 'description',
        'fee', 'commission', 'amount', 'balance'
    ]

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


class PositionAdmin(admin.ModelAdmin):
    inlines = (CashBalanceInline, AccountOrderInline, AccountTradeInline, HoldingEquityInline,
               HoldingOptionInline, ProfitLossInline)

    list_display = ('symbol', 'name', 'spread', 'status', 'start', 'stop')

    search_fields = ('symbol', 'name', 'spread', 'status', 'start', 'stop')
    list_per_page = 20

    fieldsets = (

        ('Primary Fields', {
            'fields': ('symbol', 'name', 'spread', 'status', 'start', 'stop')
        }),
    )

    def has_add_permission(self, request):
        return False


admin.site.app_index_template = 'statement/index.html'

admin.site.register(Statement, StatementAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(CashBalance, CashBalanceAdmin)
admin.site.register(AccountOrder, AccountOrderAdmin)
admin.site.register(AccountTrade, AccountTradeAdmin)
admin.site.register(HoldingEquity, HoldingEquityAdmin)
admin.site.register(HoldingOption, HoldingOptionAdmin)
admin.site.register(ProfitLoss, ProfitLossAdmin)

admin.site.register_view(
    'statement/import',
    urlname='statement_import',
    view=statement_import
)