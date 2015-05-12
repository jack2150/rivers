from django.contrib import admin
from views import *
from models import *


class StatementAdmin(admin.ModelAdmin):
    list_display = ['date', 'net_liquid', 'stock_bp', 'option_bp', 'commission_ytd']

    list_per_page = 20


class ProfitLossAdmin(admin.ModelAdmin):
    def date(self, obj):
        return obj.statement.date

    date.short_description = 'Date'
    date.admin_order_field = 'statement__date'

    list_display = [
        'date', 'symbol', 'description', 'pl_open', 'pl_pct',
        'pl_day', 'pl_ytd', 'margin_req', 'close_value',
    ]

    list_per_page = 20


admin.site.register(Statement, StatementAdmin)
admin.site.register(CashBalance)
admin.site.register(AccountOrder)
admin.site.register(AccountTrade)
admin.site.register(HoldingEquity)
admin.site.register(HoldingOption)
admin.site.register(ProfitLoss, ProfitLossAdmin)

admin.site.register_view(
    'statement/import/$',
    urlname='statement_import',
    view=statement_import
)