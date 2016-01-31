from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse
from research.algorithm.models import *
from research.algorithm.views import *


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


admin.site.register(Formula, FormulaAdmin)
admin.site.register(FormulaArgument, FormulaArgumentAdmin)

admin.site.register_view(
    'algorithm/analysis/(?P<formula_id>\d+)/(?P<argument_id>\d+)/$',
    urlname='algorithm_analysis', view=algorithm_analysis
)

# algorithm views
admin.site.register_view(
    'algorithm/report/list/(?P<symbol>\w+)/(?P<formula_id>\d+)/$',
    urlname='algorithm_report_views', view=algorithm_report_views
)
admin.site.register_view(
    'algorithm/report/json/(?P<symbol>\w+)/(?P<formula_id>\d+)/$',
    urlname='algorithm_report_json', view=algorithm_report_json
)

admin.site.register_view(
    'algorithm/report/signal/(?P<symbol>\w+)/(?P<formula_id>\d+)/(?P<backtest_id>\d+)/$',
    urlname='algorithm_signal_view', view=algorithm_signal_view
)

admin.site.register_view(
    'algorithm/report/trade/(?P<symbol>\w+)/(?P<formula_id>\d+)/(?P<backtest_id>\d+)/$',
    urlname='algorithm_trade_view', view=algorithm_trade_view
)

