from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import AdminTextareaWidget
from django.core.urlresolvers import reverse

from data.tb.final.views import reshape_h5
from research.strategy.models import Trade, Commission, TradeResult
from research.strategy.views import *


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
        'name', 'instrument', 'category', 'path', 'strategy_args'
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
    ordering = ('name', )


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
                'symbol': self.symbol.lower(), 'trade_id': self.trade.id, 'date': self.date
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

    def delete_report(self, request, queryset):
        for q in queryset.all():
            trade_result = TradeResult.objects.get(id=q.id)
            formula = Formula.objects.get(id=trade_result.formula_id)
            logger.info('Trade result: %s' % trade_result)
            symbol = trade_result.symbol.lower()
            date = trade_result.date.strftime('%Y-%m-%d')
            path = trade_result.trade.path

            fpath = os.path.join(RESEARCH_DIR, '%s.h5' % symbol)
            db = pd.HDFStore(fpath)

            def get_table(table, where):
                try:
                    df = db.select(table, where)
                except KeyError:
                    df = pd.DataFrame()
                return df

            def delete_table(table, where):
                try:
                    db.remove(table, where=where)
                except NotImplementedError:
                    db.remove(table)
                logger.info('table: %s, where: %s removed' % (table, where))

            # get strategy
            df_report1 = get_table(
                'strategy/report',
                'trade == %r & date == %r & formula == %r & report_id == %r' % (
                    path, date, formula.path, trade_result.report_id
                )
            )
            df_trade = get_table(
                'strategy/trade',
                'trade == %r & date == %r & formula == %r & report_id == %r' % (
                    path, date, formula.path, trade_result.report_id
                )
            )

            df_order = get_table(
                'strategy/order/%s' % path.replace('.', '/'),
                'trade == %r & date == %r & formula == %r & report_id == %r' % (
                    path, date, formula.path, trade_result.report_id
                )
            )

            logger.info('strategy remove, df_report: %d, df_trade: %d, df_order: %d' % (
                len(df_report1), len(df_trade), len(df_order)
            ))

            if len(df_report1):
                delete_table(
                    'strategy/report',
                    'trade == %r & date == %r & formula == %r & report_id == %r' % (
                        path, date, formula.path, trade_result.report_id
                    )
                )

            if len(df_trade):
                delete_table(
                    'strategy/trade',
                    'trade == %r & date == %r & formula == %r & report_id == %r' % (
                        path, date, formula.path, trade_result.report_id
                    )
                )

            if len(df_order):
                delete_table(
                    'strategy/order/%s' % path.replace('.', '/'),
                    'trade == %r & date == %r & formula == %r & report_id == %r' % (
                        path, date, formula.path, trade_result.report_id
                    )
                )

            db.close()

            # reshape db
            reshape_h5('%s.h5' % symbol, RESEARCH_DIR)

        queryset.delete()

    delete_report.short_description = "Delete trade results"
    actions = [delete_report]

    def get_actions(self, request):
        # Disable delete
        actions = super(TradeResultAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    list_display = (
        'date', 'symbol', 'trade', arg_keys, arg_values, 'length', report_button
    )

    fieldsets = (
        ('Foreign Key', {
            'fields': ('symbol', 'date')
        }),
        ('Primary Fields', {
            'fields': ('formula_id', 'report_id', 'trade', 'arguments', 'length')
        }),
    )

    search_fields = (
        'trade__id', 'symbol', 'date'
    )
    list_per_page = 20

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Commission, CommissionAdmin)
admin.site.register(Trade, TradeAdmin)
admin.site.register(TradeResult, TradeResultAdmin)
admin.site.register_view(
    'strategy/analysis/trade0/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/(?P<formula_id>\d+)/(?P<report_id>\d+)/$',
    urlname='strategy_analysis1', view=strategy_analysis1
)
admin.site.register_view(
    'strategy/analysis/trade1/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/(?P<formula_id>\d+)/(?P<report_id>\d+)/'
    '(?P<trade_id>\d+)/(?P<commission_id>\d+)/(?P<capital>\d+)/$',
    urlname='strategy_analysis2', view=strategy_analysis2
)

# strategy report
admin.site.register_view(
    'strategy/report/list/(?P<symbol>\w+)/(?P<trade_id>\d+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='strategy_report_view', view=strategy_report_view
)

admin.site.register_view(
    'strategy/report/json/(?P<symbol>\w+)/(?P<trade_id>\d+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='strategy_report_json', view=strategy_report_json
)

admin.site.register_view(
    'strategy/report/order/(?P<symbol>\w+)/(?P<trade_id>\d+)/(?P<report_id>\d+)/$',
    urlname='strategy_order_raw', view=strategy_order_raw
)

admin.site.register_view(
    'strategy/report/trade/(?P<symbol>\w+)/(?P<trade_id>\d+)/(?P<report_id>\d+)/$',
    urlname='strategy_trade_raw', view=strategy_trade_raw
)
