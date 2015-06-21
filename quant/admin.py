from bootstrap3_datetime.widgets import DateTimePicker
from django.contrib import admin
from django.contrib.admin.widgets import AdminTextareaWidget
from django.core.urlresolvers import reverse
from quant.models import *
from quant.views import algorithm_analysis
from django import forms


class AlgorithmForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )

    description = forms.CharField(
        widget=AdminTextareaWidget(attrs={
            'class': 'form-control vLargeTextField', 'rows': 8, 'cols': 40
        })
    )


# noinspection PyMethodMayBeStatic
class AlgorithmAdmin(admin.ModelAdmin):
    def analysis_button(self, obj):
        return '<a href="{link}">Analysis</a>'.format(
            link=reverse('admin:algorithm_analysis', kwargs={'algorithm_id': obj.id})
        )

    analysis_button.short_description = ''
    analysis_button.allow_tags = True

    form = AlgorithmForm
    list_display = ('rule', 'date', 'category', 'method',
                    'fname', 'formula', 'analysis_button')

    fieldsets = (
        ('Primary Fields', {
            'fields': ('rule', 'formula', 'date', 'category',
                       'method', 'fname', 'description')
        }),
    )

    search_fields = ('rule', 'formula', 'date', 'category', 'method', 'fname')
    list_per_page = 20


# noinspection PyMethodMayBeStatic
class AlgorithmResultAdmin(admin.ModelAdmin):
    def short_arguments(self, obj):
        arguments = eval(obj.arguments)

        return arguments.values()

    short_arguments.short_description = 'Arguments'

    form = AlgorithmForm
    list_display = (
        'symbol', 'date', 'algorithm', 'short_arguments', 'sharpe_spy',
        'buy_hold', 'trades', 'profit_prob', 'loss_prob', 'sum_result', 'var_pct99'
    )

    fieldsets = (
        ('Foreign Key', {
            'fields': ('symbol', 'date', 'algorithm', 'arguments')
        }),
        ('Primary Fields', {
            'fields': (
                'sharpe_rf', 'sharpe_spy', 'sortino_rf', 'sortino_spy',
                'buy_hold', 'trades', 'profit_trades', 'profit_prob',
                'loss_trades', 'loss_prob', 'max_profit', 'max_loss',
                'sum_result', 'cumprod_result', 'mean_result',
                'var_pct99', 'var_pct95', 'signals')
        }),
    )

    search_fields = (
        'symbol', 'date', 'arguments',
        'algorithm__id', 'algorithm__rule'
    )
    list_per_page = 20

    readonly_fields = ('algorithm', )

    def has_add_permission(self, request):
        return False


admin.site.register(Algorithm, AlgorithmAdmin)
admin.site.register(AlgorithmResult, AlgorithmResultAdmin)

admin.site.register_view(
    'quant/algorithm/analysis/(?P<algorithm_id>\d)/$',
    urlname='algorithm_analysis', view=algorithm_analysis
)

