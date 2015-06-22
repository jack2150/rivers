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
    list_display = ('rule', 'date', 'category', 'method', 'formula', 'analysis_button')

    fieldsets = (
        ('Primary Fields', {
            'fields': ('rule', 'formula', 'date', 'category',
                       'method', 'path', 'description')
        }),
    )

    search_fields = ('rule', 'formula', 'date', 'category', 'method')
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
        'bh_sum', 'pl_sum',
        'bh_cumprod', 'pl_cumprod',
        'trades', 'profit_prob', 'loss_prob',
        'max_dd', 'var_pct99'
    )

    fieldsets = (
        ('Foreign Key', {
            'fields': ('symbol', 'date', 'algorithm', 'arguments')
        }),
        ('Primary Fields', {
            'fields': (
                'sharpe_rf', 'sharpe_spy', 'sortino_rf', 'sortino_spy',
                'buy_hold', 'bh_cumprod',
                'trades', 'profit_trades', 'profit_prob',
                'loss_trades', 'loss_prob', 'max_profit', 'max_loss',
                'pl_sum', 'pl_cumprod', 'pl_mean',
                'var_pct99', 'var_pct95',
                'max_dd', 'r_max_dd', 'max_bh_dd', 'r_max_bh_dd',
                'signals')
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

