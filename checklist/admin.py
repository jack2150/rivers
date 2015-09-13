from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.contrib import admin
from checklist.views import *


class EnterOpinionForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )
    enter_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )
    exit_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


# noinspection PyMethodMayBeStatic
class EnterOpinionAdmin(admin.ModelAdmin):
    form = EnterOpinionForm
    #change_form_template = 'checklist/enter_opinion/change_form.html'

    def action(self, obj):
        href = """
        <div class="dropdown">
          <button class="btn btn-default btn-xs dropdown-toggle" type="button"
            id="dropdownMenu1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
            Action
            <span class="caret"></span>
          </button>
          <ul class="dropdown-menu" aria-labelledby="dropdownMenu1">
            <li><a href="{get_data_link}">Get data</a></li>
            <li class="divider"></li>
            <li><a href="{report_link}">Report</a></li>
          </ul>
        </div>
        """
        return href.format(
            get_data_link=reverse('admin:enter_opinion_get_data', kwargs={'id': obj.id}),
            report_link=reverse('admin:enter_opinion_report', kwargs={'id': obj.id}),
        )

    action.short_description = ''
    action.allow_tags = True

    list_display = (
        'symbol', 'date', 'risk_profile', 'signal', 'target', 'profit', 'loss',
        'score', 'complete', 'trade', 'action'
    )

    fieldsets = (
        ('Primary field', {
            'fields': (
                'position',  'symbol', 'date', 'score', 'complete', 'trade'
            )
        }),
        ('Position', {
            'fields': (
                'risk_profile', 'bp_effect', 'profit', 'loss', 'size',
                'strategy', 'optionable', 'spread', 'enter_date', 'exit_date'
            )
        }),
        ('Trade signal', {
            'fields': (
                'signal', 'event', 'significant', 'confirm', 'target', 'market', 'description'
            )
        }),
        ('Event', {
            'fields': (
                'earning', 'dividend', 'split', 'announcement'
            )
        }),
        ('News', {
            'fields': (
                'news_level', 'news_signal'
            )
        }),
        ('Trend', {
            'fields': (
                'long_trend0', 'long_trend1', 'short_trend0', 'short_trend1',
                'long_persist', 'short_persist'
            )
        }),
        ('Ownership', {
            'fields': (
                'ownership',
                'ownership_holding_pct',
                'ownership_sell_count', 'ownership_sell_share',
                'ownership_held_count', 'ownership_held_share',
                'ownership_buy_count', 'ownership_buy_share',
                'ownership_na', 'ownership_na_pct',
                'ownership_new_count', 'ownership_new_share',
                'ownership_out_count', 'ownership_out_share',
                'ownership_top15_sum', 'ownership_top15_na_pct',
            )
        }),
        ('Insider', {
            'fields': (
                'insider',
                'insider_buy_3m', 'insider_buy_12m',
                'insider_sell_3m', 'insider_sell_12m',
                'insider_buy_share_3m', 'insider_buy_share_12m',
                'insider_sell_share_3m', 'insider_sell_share_12m',
                'insider_na_3m', 'insider_na_12m',
            )
        }),
        ('Short interest', {
            'fields': (
                'short_interest', 'df_short_interest', 'short_squeeze'
            )
        }),
        ('Analyst Rating', {
            'fields': (
                'analyst_rating', 'abr_current', 'abr_previous', 'abr_target', 'abr_rating_count'
            )
        }),
    )

    search_fields = ('symbol', )
    list_filter = ('complete', 'trade', 'signal', 'significant', 'confirm')
    list_per_page = 20


class DateForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


class MarketOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'date', 'long_trend1', 'short_trend1', 'long_persist', 'volatility',
        'market_indicator', 'extra_attention', 'key_indicator', 'special_news',
        'description',
    )

    fieldsets = (
        ('Primary field', {
            'fields': (
                'date',
            )
        }),
        ('Trend', {
            'fields': (
                'short_trend0', 'short_trend1', 'long_trend0', 'long_trend1',
                'short_persist', 'long_persist', 'description'
            )
        }),
        ('Market', {
            'fields': (
                'volatility', 'bond', 'commodity', 'currency',
            )
        }),
        ('Calendar', {
            'fields': (
                'market_indicator', 'extra_attention', 'key_indicator',
                'special_news', 'commentary'
            )
        }),
    )

    search_fields = ('date', )
    list_per_page = 20


class ExitOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    def symbol(self, obj):
        return obj.position.symbol

    list_display = (
        'symbol', 'date', 'auto_trigger', 'condition', 'result',
        'amount', 'price', 'timing', 'wait'
    )

    fieldsets = (
        ('Primary field', {
            'fields': (
                'position', 'date'
            )
        }),
        ('Trade', {
            'fields': (
                'auto_trigger', 'condition', 'result', 'amount', 'price',
                'timing', 'wait', 'description'
            )
        }),
    )

    search_fields = ('position__symbol', 'date', 'description')
    list_filter = ('auto_trigger', 'condition', 'result', 'timing', 'wait')
    list_per_page = 20


# noinspection PyMethodMayBeStatic
class HoldingOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    def symbol(self, obj):
        return obj.position.symbol

    list_display = (
        'symbol', 'date', 'condition', 'action', 'opinion',
        'news_level', 'news_effect', 'special'
    )

    fieldsets = (
        ('Primary field', {
            'fields': (
                'position', 'date'
            )
        }),
        ('Position', {
            'fields': (
                'check_all', 'condition', 'action', 'opinion',
                'news_level', 'news_effect', 'special', 'description'
            )
        }),
    )

    search_fields = ('position__symbol', 'date', 'description')
    list_filter = ('condition', 'news_level', 'news_effect', 'check_all', 'special')
    list_per_page = 20

    def has_add_permission(self, request):
        return False


admin.site.register(MarketOpinion, MarketOpinionAdmin)
admin.site.register(EnterOpinion, EnterOpinionAdmin)
admin.site.register(ExitOpinion, ExitOpinionAdmin)
admin.site.register(HoldingOpinion, HoldingOpinionAdmin)


admin.site.register_view(
    'checklist/enteropinion/get_data/(?P<id>\d+)/$',
    urlname='enter_opinion_get_data', view=enter_opinion_get_data
)
admin.site.register_view(
    'checklist/enteropinion/report/(?P<id>\d+)/$',
    urlname='enter_opinion_report', view=enter_opinion_report
)
admin.site.register_view(
    'checklist/enteropinion/link/(?P<symbol>\w+)/$',
    urlname='enter_opinion_links', view=enter_opinion_links
)

