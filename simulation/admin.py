from bootstrap3_datetime.widgets import DateTimePicker
from django.contrib import admin
from django.contrib.admin.widgets import AdminTextareaWidget
from simulation.models import *
from simulation.views import *


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
class StrategyAdmin(admin.ModelAdmin):
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


class StrategyResultForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )

    df_trade = forms.CharField(
        widget=AdminTextareaWidget(attrs={
            'class': 'form-control vLargeTextField', 'rows': 8, 'cols': 40, 'wrap': 'off'
        })
    )

    df_cumprod = forms.CharField(
        widget=AdminTextareaWidget(attrs={
            'class': 'form-control vLargeTextField', 'rows': 8, 'cols': 40, 'wrap': 'off'
        })
    )


# noinspection PyMethodMayBeStatic
class StrategyResultAdmin(admin.ModelAdmin):
    form = StrategyResultForm

    def algorithm(self, obj):
        return obj.algorithm_result.algorithm

    algorithm.admin_order_field = 'algorithm_result__algorithm'

    def algorithm_args(self, obj):
        arguments = eval(obj.algorithm_result.arguments)

        handle_data = arguments['handle_data']
        create_signal = arguments['create_signal']

        return handle_data.values() + create_signal.values()

    algorithm_args.admin_order_field = 'algorithm_result__arguments'
    algorithm_args.short_description = 'Args0'

    def short_args(self, obj):
        try:
            args = sorted(eval(obj.arguments).values(), reverse=True)
        except AttributeError:
            args = []
        return args

    short_args.short_description = 'Args1'
    short_args.admin_order_field = 'arguments'

    list_display = (
        'strategy', 'short_args', 'algorithm', 'algorithm_args',
        'symbol', 'sharpe_spy', 'pl_sum',
        'trades', 'profit_prob', 'loss_prob',
        'capital0', 'roi_mean'
    )
    fieldsets = (
        ('Foreign Key', {
            'fields': (
                'algorithm_result',  'commission', 'date'
            )
        }),
        ('Strategy Fields', {
            'fields': (
                'strategy', 'arguments'
            )
        }),
        ('Report Fields', {
            'fields': (
                'sharpe_rf', 'sharpe_spy', 'sortino_rf', 'sortino_spy',
                'bh_sum', 'bh_cumprod',
                'trades', 'profit_trades', 'profit_prob',
                'loss_trades', 'loss_prob', 'max_profit', 'max_loss',
                'pl_sum', 'pl_cumprod', 'pl_mean',
                'var_pct99', 'var_pct95',
                'max_dd', 'r_max_dd', 'max_bh_dd', 'r_max_bh_dd',
                'pct_mean', 'pct_median', 'pct_max', 'pct_min', 'pct_std',
                'day_profit_mean', 'day_loss_mean',
                'df_trade', 'df_cumprod'
            )
        }),
        ('Trade Fields', {
            'fields': (
                'capital0', 'capital1', 'cumprod1',
                'remain_mean', 'cp_remain_mean',
                'fee_mean', 'fee_sum',
                'roi_mean', 'roi_sum', 'cp_roi_mean', 'cp_roi_sum',
            ),
        }),
    )

    search_fields = (
        'algorithm_result__algorithm__rule', 'algorithm_result__algorithm__id',
        'algorithm_result__arguments', 'algorithm_result__symbol',
        'strategy__name', 'arguments'
    )
    list_filter = ('strategy__instrument', 'strategy__category')
    readonly_fields = ('algorithm_result', 'strategy', 'commission')
    list_per_page = 20


admin.site.register(Commission, CommissionAdmin)
admin.site.register(Strategy, StrategyAdmin)
admin.site.register(StrategyResult, StrategyResultAdmin)

admin.site.register_view(
    'simulation/strategy/analysis/select/(?P<algorithmresult_id>\d+)/$',
    urlname='strategy_analysis1', view=strategy_analysis1
)
admin.site.register_view(
    'simulation/strategy/analysis/args/(?P<algorithmresult_id>\d+)/(?P<strategy_id>\d+)/$',
    urlname='strategy_analysis2', view=strategy_analysis2
)
