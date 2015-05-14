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

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CashBalanceInline(StatementInline):
    model = CashBalance

    fields = ('time', 'name', 'ref_no', 'description',
              'fee', 'commission', 'amount', 'balance')
    readonly_fields = ('time', 'name', 'ref_no', 'description',
                       'fee', 'commission', 'amount', 'balance')


class AccountOrderInline(StatementInline):
    model = AccountOrder

    fields = ('time', 'spread', 'side', 'qty', 'pos_effect', 'symbol',
              'exp', 'strike', 'contract', 'price', 'order', 'tif', 'status')

    readonly_fields = ('time', 'spread', 'side', 'qty', 'pos_effect', 'symbol',
                       'exp', 'strike', 'contract', 'price', 'order', 'tif', 'status')


class AccountTradeInline(StatementInline):
    model = AccountTrade

    fields = ('time', 'spread', 'side', 'qty', 'pos_effect', 'symbol', 'exp',
              'strike', 'contract', 'price', 'net_price', 'order_type')

    readonly_fields = ('time', 'spread', 'side', 'qty', 'pos_effect', 'symbol', 'exp',
                       'strike', 'contract', 'price', 'net_price', 'order_type')


class HoldingEquityInline(StatementInline):
    model = HoldingEquity

    fields = ('symbol', 'description', 'qty', 'trade_price', 'close_price', 'close_value')

    readonly_fields = ('symbol', 'description', 'qty', 'trade_price', 'close_price', 'close_value')

    ordering = ('symbol', )


class HoldingOptionInline(StatementInline):
    model = HoldingOption

    fields = ('symbol', 'option_code', 'exp', 'strike', 'contract',
              'qty', 'trade_price', 'close_price', 'close_value')

    readonly_fields = ('symbol', 'option_code', 'exp', 'strike', 'contract',
                       'qty', 'trade_price', 'close_price', 'close_value')

    ordering = ('symbol', )


class ProfitLossInline(StatementInline):
    model = ProfitLoss

    fields = ('symbol', 'description', 'pl_open', 'pl_pct',
              'pl_day', 'pl_ytd', 'margin_req', 'close_value')

    readonly_fields = ('symbol', 'description', 'pl_open', 'pl_pct',
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
                'statement',
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


class AccountOrderAdmin(StatementModelAdmin):
    form = StatementForm  # enable bootstrap datetime js

    list_display = [
        'date', 'time', 'spread', 'side', 'qty', 'pos_effect', 'symbol',
        'exp', 'strike', 'contract', 'price', 'order', 'tif', 'status'
    ]

    fieldsets = (
        ('Foreign Keys', {
            'fields': (
                'statement',
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

    list_filter = ('spread', 'pos_effect', 'contract', 'order', 'tif')

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
                'statement',
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
                'statement',
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
                'statement',
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
                'statement',
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


admin.site.app_index_template = 'statement/index.html'

admin.site.register(Statement, StatementAdmin)
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