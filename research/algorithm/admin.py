from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db.models import QuerySet

from data.tb.final.views import reshape_h5
from research.algorithm.models import *
from research.algorithm.views import *
from research.strategy.models import TradeResult


class FormulaForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


# noinspection PyMethodMayBeStatic
class FormulaAdmin(admin.ModelAdmin):
    def analysis_button(self, obj):
        return '<a href="{link}">Analysis</a>'.format(
            link=reverse('admin:algorithm_analysis', kwargs={
                'formula_id': obj.id, 'argument_id': 0
            })
        )

    analysis_button.short_description = ''
    analysis_button.allow_tags = True

    form = FormulaForm
    list_display = ('rule', 'date', 'category', 'method',
                    'equation', 'optionable', 'analysis_button')

    fieldsets = (
        ('Primary Fields', {
            'fields': ('rule', 'equation', 'date', 'category',
                       'method', 'path', 'optionable', 'description')
        }),
    )

    search_fields = ('rule', 'equation', 'date', 'category', 'method')
    list_filter = ('category', )
    list_per_page = 20


# noinspection PyMethodMayBeStatic
class FormulaArgumentAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        """
        Don't allow adding new Product Categories
        :param request: request
        :param obj: FormulaArgument
        :param kwargs: dict
        """
        form = super(FormulaArgumentAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['formula'].widget.can_add_related = False
        return form

    def analysis_button(self, obj):
        return '<a href="{link}">Analysis</a>'.format(
            link=reverse('admin:algorithm_analysis', kwargs={
                'formula_id': obj.formula.id, 'argument_id': obj.id
            })
        )

    analysis_button.short_description = ''
    analysis_button.allow_tags = True

    def arg_keys(self, obj):
        return [k.split('_')[-1] for k in eval(obj.arguments).keys()]

    arg_keys.short_description = 'Arguments'
    arg_keys.admin_order_field = 'arguments'

    def arg_values(self, obj):
        return eval(obj.arguments).values()

    arg_values.short_description = 'Values'
    arg_values.admin_order_field = 'arguments'

    list_display = ('formula', 'level', 'arg_keys', 'arg_values', 'result', 'analysis_button')

    fieldsets = (
        ('Foreign Key', {
            'fields': ('formula', )
        }),
        ('Primary Fields', {
            'fields': ('arguments', 'level', 'result', 'description')
        }),
    )

    search_fields = (
        'formula__id', 'formula__rule', 'level', 'result', 'description'
    )
    list_filter = ('level', 'result')
    list_per_page = 20


# noinspection PyMethodMayBeStatic
class FormulaResultAdmin(admin.ModelAdmin):
    form = FormulaForm

    def report_button(self):
        return '<a href="{link}">Report</a>'.format(
            link=reverse('admin:algorithm_report_view', kwargs={
                'symbol': self.symbol.lower(), 'formula_id': self.formula.id, 'date': self.date
            })
        )

    report_button.short_description = ''
    report_button.allow_tags = True

    def delete_report(self, request, queryset):
        for q in queryset.all():
            formula_result = FormulaResult.objects.get(id=q.id)
            logger.info('Formula result: %s' % formula_result)
            symbol = formula_result.symbol.lower()
            date = formula_result.date
            path = formula_result.formula.path

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

            # get algorithm
            df_report0 = get_table('algorithm/report', 'formula == %r & date == %r' % (
                path, date
            ))

            df_signal = get_table('algorithm/signal', 'formula == %r & date == %r' % (
                path, date
            ))
            logger.info('algorithm remove df_report: %d, df_signal: %d' % (
                len(df_report0), len(df_signal)
            ))

            # get strategy
            df_report1 = get_table('strategy/report', 'formula == %r & date == %r' % (
                path, date
            ))
            df_trade = get_table('strategy/trade', 'formula == %r & date == %r' % (
                path, date
            ))

            trades = df_report1['trade'].unique()
            orders = []
            for trade in trades:
                df_temp = get_table(
                    'strategy/order/%s' % trade.replace('.', '/'),
                    'formula == %r & date == %r & trade == %r' % (
                        path, date, trade
                    )
                )
                orders.append(df_temp)
            df_order = pd.concat(orders)
            """ :type: pd.DataFrame """
            logger.info('strategy remove, df_report: %d, df_trade: %d, df_order: %d' % (
                len(df_report1), len(df_trade), len(df_order)
            ))

            try:
                # delete algorithm
                if len(df_report0):
                    delete_table('algorithm/report', 'formula == %r & date == %r' % (
                        path, date
                    ))
                if len(df_signal):
                    delete_table('algorithm/signal', 'formula == %r & date == %r' % (
                        path, date
                    ))

                # delete strategy
                if len(df_report1):
                    delete_table('strategy/report', 'formula == %r & date == %r' % (
                        path, date
                    ))

                if len(df_report1):
                    delete_table('strategy/trade', 'formula == %r & date == %r' % (
                        path, date
                    ))

                if len(df_order):
                    trades = df_report1['trade'].unique()
                    for trade in trades:
                        delete_table(
                            'strategy/order/%s' % trade.replace('.', '/'),
                            'formula == %r & date == %r & trade == %r' % (path, date, trade)
                        )
            except KeyError:
                pass

            db.close()

            # remove strategy result
            trade_results = TradeResult.objects.filter(
                Q(symbol=symbol.upper()) & Q(date=date) &
                Q(formula_id=formula_result.formula.id)
            )
            trade_results.delete()

            # reshape db
            reshape_h5('%s.h5' % symbol, RESEARCH_DIR)

        queryset.delete()

    delete_report.short_description = "Delete formula results"
    actions = [delete_report]

    def get_actions(self, request):
        # Disable delete
        actions = super(FormulaResultAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def arg_keys(self):
        return [k.split('_')[-1] for k in eval(self.arguments).keys()]

    arg_keys.short_description = 'Arguments'
    arg_keys.admin_order_field = 'arguments'

    def arg_values(self):
        return eval(self.arguments).values()

    arg_values.short_description = 'Values'
    arg_values.admin_order_field = 'arguments'

    list_display = (
        'date', 'symbol', 'formula', arg_keys, arg_values, 'length', report_button
    )

    fieldsets = (
        ('Foreign Key', {
            'fields': ('symbol', 'date')
        }),
        ('Primary Fields', {
            'fields': ('formula', 'arguments', 'length')
        }),
    )

    search_fields = (
        'formula__id', 'symbol', 'date'
    )
    list_per_page = 20

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Formula, FormulaAdmin)
admin.site.register(FormulaArgument, FormulaArgumentAdmin)
admin.site.register(FormulaResult, FormulaResultAdmin)

admin.site.register_view(
    'algorithm/analysis/formula/(?P<formula_id>\d+)/(?P<argument_id>\d+)/$',
    urlname='algorithm_analysis', view=algorithm_analysis
)

# algorithm views
admin.site.register_view(
    'algorithm/report/list/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/(?P<formula_id>\d+)/$',
    urlname='algorithm_report_view', view=algorithm_report_view
)

admin.site.register_view(
    'algorithm/report/json/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/(?P<formula_id>\d+)/$',
    urlname='algorithm_report_json', view=algorithm_report_json
)

admin.site.register_view(
    'algorithm/report/signal/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/(?P<formula_id>\d+)/(?P<report_id>\d+)/$',
    urlname='algorithm_signal_view', view=algorithm_signal_view
)

admin.site.register_view(
    'algorithm/report/trade/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/(?P<formula_id>\d+)/(?P<report_id>\d+)/$',
    urlname='algorithm_trade_view', view=algorithm_trade_view
)

admin.site.register_view(
    'strategy/report/formula/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/(?P<formula_id>\d+)/(?P<report_id>\d+)/$',
    urlname='algorithm_signal_raw', view=algorithm_signal_raw
)
