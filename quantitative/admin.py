from bootstrap3_datetime.widgets import DateTimePicker
from django.contrib import admin
from django.contrib.admin.widgets import AdminTextareaWidget
from django.core.urlresolvers import reverse
from quantitative.models import *
from quantitative.views import algorithm_analysis
from django import forms


class AlgorithmForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


# noinspection PyMethodMayBeStatic
class AlgorithmAdmin(admin.ModelAdmin):
    def analysis_button(self, obj):
        return '<a href="{link}">Analysis</a>'.format(
            link=reverse('admin:algorithm_analysis', kwargs={
                'algorithm_id': obj.id, 'argument_id': 0
            })
        )

    analysis_button.short_description = ''
    analysis_button.allow_tags = True

    form = AlgorithmForm
    list_display = ('rule', 'date', 'category', 'method',
                    'formula', 'optionable', 'analysis_button')

    fieldsets = (
        ('Primary Fields', {
            'fields': ('rule', 'formula', 'date', 'category',
                       'method', 'path', 'optionable', 'description')
        }),
    )

    search_fields = ('rule', 'formula', 'date', 'category', 'method')
    list_filter = ('category', )
    list_per_page = 20


# noinspection PyMethodMayBeStatic
class AlgorithmArgumentAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        """
        Don't allow adding new Product Categories
        """
        form = super(AlgorithmArgumentAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['algorithm'].widget.can_add_related = False
        return form

    def analysis_button(self, obj):
        return '<a href="{link}">Analysis</a>'.format(
            link=reverse('admin:algorithm_analysis', kwargs={
                'algorithm_id': obj.algorithm.id, 'argument_id': obj.id
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

    list_display = ('algorithm', 'level', 'arg_keys', 'arg_values', 'result', 'analysis_button')

    fieldsets = (
        ('Foreign Key', {
            'fields': ('algorithm', )
        }),
        ('Primary Fields', {
            'fields': ('arguments', 'level', 'result', 'description')
        }),
    )

    search_fields = (
        'algorithm__id', 'algorithm__rule', 'level', 'result', 'description'
    )
    list_filter = ('level', 'result')
    list_per_page = 20


class AlgorithmResultForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )

    df_signal = forms.CharField(
        widget=AdminTextareaWidget(attrs={
            'class': 'form-control vLargeTextField', 'rows': 8, 'cols': 40, 'wrap': 'off'
        })
    )


# noinspection PyMethodMayBeStatic
class AlgorithmResultAdmin(admin.ModelAdmin):
    form = AlgorithmResultForm

    def short_arguments(self, obj):
        arguments = eval(obj.arguments)

        handle_data = arguments['handle_data']
        create_signal = arguments['create_signal']

        return handle_data.values() + create_signal.values()

    short_arguments.short_description = 'Args'
    short_arguments.admin_order_field = 'arguments'

    def manage(self, obj):
        href = """
            <div class="dropdown">
              <button class="btn btn-default btn-xs dropdown-toggle" type="button"
                id="dropdownMenu1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
                Manage
                <span class="caret"></span>
              </button>
              <ul class="dropdown-menu" aria-labelledby="dropdownMenu1">
                <li><a href="{analysis}">Strategy Analysis</a></li>
                <li><a href="{df_view}">Dataframe</a></li>
              </ul>
            </div>
            """
        return href.format(
            analysis=reverse('admin:strategy_analysis1', kwargs={'algorithmresult_id': obj.id}),
            df_view=reverse('admin:df_view', kwargs={'model': 'algorithm', 'id': obj.id}),
        )

    manage.short_description = ''
    manage.allow_tags = True

    list_display = (
        'algorithm', 'short_arguments', 'symbol', 'sharpe_spy',
        'bh_sum', 'pl_sum',
        'bh_cumprod', 'pl_cumprod',
        'trades', 'profit_prob', 'loss_prob',
        'max_dd', 'var_pct99',
        'manage'
    )

    fieldsets = (
        ('Foreign Key', {
            'fields': ('algorithm', )
        }),
        ('Arguments', {
            'fields': (
                'arguments',
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
                'pct_bull', 'pct_even', 'pct_bear',
                'df_signal')
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
admin.site.register(AlgorithmArgument, AlgorithmArgumentAdmin)
admin.site.register(AlgorithmResult, AlgorithmResultAdmin)

admin.site.register_view(
    'quant/algorithm/analysis/(?P<algorithm_id>\d+)/(?P<argument_id>\d+)/$',
    urlname='algorithm_analysis', view=algorithm_analysis
)

