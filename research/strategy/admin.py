from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminTextareaWidget
from django.core.urlresolvers import reverse

from research.strategy.models import Trade, Commission, TradeResult
from research.strategy.views import strategy_analysis1, strategy_analysis2, strategy_report_view, strategy_report_json


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


class TradeForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


# noinspection PyMethodMayBeStatic
class TradeResultAdmin(admin.ModelAdmin):
    form = TradeForm

    def report_button(self):
        return '<a href="{link}">Report</a>'.format(
            link=reverse('admin:strategy_report_view', kwargs={
                'symbol': self.symbol.lower(), 'trade_id': self.trade.id
            })
        )

    report_button.short_description = ''
    report_button.allow_tags = True

    report_button.short_description = ''
    report_button.allow_tags = True

    def arg_keys(self):
        return ','.join([str(v) for v in eval(self.arguments).keys()])

    arg_keys.short_description = 'Arguments'
    arg_keys.admin_order_field = 'arguments'

    def arg_values(self):
        return ','.join([str(v) for v in eval(self.arguments).values()])

    arg_values.short_description = 'Values'
    arg_values.admin_order_field = 'arguments'

    list_display = (
        'date', 'symbol', 'trade', arg_keys, arg_values, 'length', report_button
    )

    fieldsets = (
        ('Foreign Key', {
            'fields': ('symbol', 'trade')
        }),
        ('Primary Fields', {
            'fields': ('date', 'arguments', 'length')
        }),
    )

    search_fields = (
        'trade__id', 'symbol', 'date'
    )
    list_per_page = 20


admin.site.register(Commission, CommissionAdmin)
admin.site.register(Trade, TradeAdmin)
admin.site.register(TradeResult, TradeResultAdmin)
admin.site.register_view(
    'strategy/analysis/trade/(?P<symbol>\w+)/(?P<formula_id>\d+)/(?P<backtest_id>\d+)/$',
    urlname='strategy_analysis1', view=strategy_analysis1
)
admin.site.register_view(
    'strategy/analysis/arguments/(?P<symbol>\w+)/(?P<formula_id>\d+)/(?P<backtest_id>\d+)/'
    '(?P<trade_id>\d+)/(?P<commission_id>\d+)/(?P<capital>\d+)/$',
    urlname='strategy_analysis2', view=strategy_analysis2
)

# strategy report
admin.site.register_view(
    'strategy/report/list/(?P<symbol>\w+)/(?P<trade_id>\d+)/$',
    urlname='strategy_report_view', view=strategy_report_view
)

admin.site.register_view(
    'strategy/report/json/(?P<symbol>\w+)/(?P<trade_id>\d+)/$',
    urlname='strategy_report_json', view=strategy_report_json
)
