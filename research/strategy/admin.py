from bootstrap3_datetime.widgets import DateTimePicker
from django.contrib import admin
from django.contrib.admin.widgets import AdminTextareaWidget

from research.strategy.models import Trade, Commission
from research.strategy.views import strategy_analysis1, strategy_analysis2


class CommissionAdmin(admin.ModelAdmin):
    list_display = (
        'company', 'plan',
        'stock_order_fee', 'stock_brokerage_fee',
        'option_order_fee', 'option_contract_fee',
    )

    fieldsets = (
        ('Primary Fields', {
            'fields': (
                'company', 'plan',
                'stock_order_fee', 'stock_brokerage_fee',
                'option_order_fee', 'option_contract_fee',
            )
        }),
    )

    search_fields = ('company', 'plan')
    list_per_page = 20


# noinspection PyMethodMayBeStatic,PyBroadException
class TradeAdmin(admin.ModelAdmin):
    def strategy_args(self, obj):
        try:
            args = sorted(eval(obj.arguments).values(), reverse=True)
        except Exception:
            args = []
        return args

    strategy_args.short_description = 'Args'
    strategy_args.admin_order_field = 'arguments'

    list_display = (
        'name', 'instrument', 'category', 'description', 'path', 'strategy_args'
    )
    fieldsets = (
        ('Primary Fields', {
            'fields': (
                'name', 'instrument', 'category', 'description', 'path', 'arguments'
            )
        }),
    )

    search_fields = ('name', 'instrument', 'category', 'description')
    list_filter = ('instrument', 'category')
    list_per_page = 20


admin.site.register(Commission, CommissionAdmin)
admin.site.register(Trade, TradeAdmin)
admin.site.register_view(
    'strategy/analysis/trade/(?P<symbol>\w+)/(?P<formula_id>\d+)/(?P<report_id>\d+)/$',
    urlname='strategy_analysis1', view=strategy_analysis1
)
admin.site.register_view(
    'strategy/analysis/arguments/(?P<symbol>\w+)/(?P<formula_id>\d+)/(?P<report_id>\d+)/'
    '(?P<trade_id>\d+)/(?P<commission_id>\d+)/(?P<capital>\d+)/$',
    urlname='strategy_analysis2', view=strategy_analysis2
)

