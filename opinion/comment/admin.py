from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.contrib import admin
from base.admin import DateForm
from opinion.comment.models import PortfolioOpinion, PositionOpinion, WeekdayOpinion, CloseOpinion
from opinion.comment.views import weekday_profile, position_profile


class PortfolioOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'date', 'trades', 'pl_ytd', 'performance'
    )
    fieldsets = (
        ('Primary', {'fields': ('date', )}),
        ('Portfolio', {'fields': ('trades', 'pl_ytd', 'performance')}),
        ('Description', {'fields': ('emotion', 'position', 'movement', 'expectation', 'research')}),
    )

    search_fields = (
        'emotion', 'position', 'movement', 'expectation', 'research'
    )
    list_filter = ('performance', )

    list_per_page = 20


class PositionOpinionForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )
    enter_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )
    exit_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


class PositionOpinionAdmin(admin.ModelAdmin):
    form = PositionOpinionForm

    list_display = (
        'symbol', 'date', 'price_movement', 'event_trade',
        'risk_profile', 'bp_effect', 'max_profit', 'max_loss', 'size',
        'strategy', 'spread', 'optionable',
    )
    fieldsets = (
        ('Primary', {
            'fields': (
                'symbol', 'date',
            )
        }),
        ('Signal', {
            'fields': (
                'price_movement', 'event_trade', 'target_price',
            )
        }),
        ('Position', {
            'fields': (
                'risk_profile', 'bp_effect', 'max_profit', 'max_loss', 'size',
                'strategy', 'spread', 'optionable',
            )
        }),
        ('Timing', {
            'fields': (
                'enter_date', 'exit_date', 'dte',
            )
        }),
        ('Others', {
            'fields': (
                'event_period', 'description',
            )
        }),
    )

    search_fields = (
        'symbol', 'date', 'strategy', 'enter_date', 'exit_date',
    )
    list_filter = (
        'price_movement', 'event_trade', 'risk_profile', 'spread',
        'optionable', 'event_period',
    )
    list_per_page = 20


class CloseOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'symbol', 'date', 'auto_trigger', 'condition', 'result',
        'amount', 'stock_price', 'timing', 'wait'
    )
    fieldsets = (
        ('Primary', {
            'fields': (
                'symbol', 'date'
            )
        }),
        ('Position', {
            'fields': (
                'auto_trigger', 'condition', 'result', 'amount', 'stock_price',
                'timing', 'wait', 'others'
            )
        }),
    )

    search_fields = ('symbol', 'date', 'others')
    list_filter = ('auto_trigger', 'condition', 'result', 'timing', 'wait')
    list_per_page = 20


class WeekdayOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'symbol', 'date', 'close_price', 'new_info_impact',
        'today_iv', 'iv_rank', 'put_call_ratio',
        'position_stage', 'position_hold', 'position_action',
    )
    fieldsets = (
        ('Primary', {
            'fields': (
                'symbol', 'date', 'close_price'
            )
        }),
        ('New information', {
            'fields': (
                'new_info_impact', 'new_info_move', 'new_info_desc',
            )
        }),
        ('Today Option Stat', {
            'fields': (
                'today_iv', 'iv_rank', 'hv_rank', 'put_call_ratio', 'today_biggest', 'sizzle_index',
            )
        }),
        ('Statistical', {
            'fields': (
                'last_5day_return', 'consecutive_move', 'unusual_volume', 'moving_avg200x50',
                'weekend_effect',
            )
        }),

        ('Price Movement', {
            'fields': (
                'previous_short_trend', 'current_short_trend',
                'previous_long_trend', 'current_long_trend',
            )
        }),
        ('Position', {
            'fields': (
                'position_stage', 'position_hold', 'position_action',
            )
        }),
        ('Others', {
            'fields': (
                'short_squeeze', 'others',
            )
        }),
    )

    search_fields = ('symbol', 'date', 'new_info_desc', 'others')
    list_filter = (
        'new_info_impact', 'new_info_move',
        'iv_rank', 'hv_rank', 'today_biggest',
        'consecutive_move', 'unusual_volume', 'moving_avg200x50', 'weekend_effect',
        'previous_short_trend', 'current_short_trend',
        'previous_long_trend', 'current_long_trend',
        'position_stage', 'position_hold', 'position_action',
        'short_squeeze',
    )
    list_per_page = 20


admin.site.register(PortfolioOpinion, PortfolioOpinionAdmin)
admin.site.register(PositionOpinion, PositionOpinionAdmin)
admin.site.register(WeekdayOpinion, WeekdayOpinionAdmin)
admin.site.register(CloseOpinion, CloseOpinionAdmin)

admin.site.register_view(
    'opinion/profile/weekday/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='weekday_profile', view=weekday_profile
)
admin.site.register_view(
    'opinion/profile/position/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='position_profile', view=position_profile
)
