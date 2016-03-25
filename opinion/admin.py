from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.contrib import admin
from opinion.views import *


class DateForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


class MarketMovementAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'date', 'current_long_trend', 'current_short_trend', 'volatility',
        'market_indicator', 'extra_attention', 'key_indicator', 'special_news'
    )

    fieldsets = (
        ('Primary', {
            'fields': (
                'date',
            )
        }),
        ('Stock Market', {
            'fields': (
                'previous_short_trend', 'current_short_trend',
                'previous_long_trend', 'current_long_trend'
            )
        }),
        ('Major Market', {
            'fields': (
                'volatility', 'bond', 'commodity', 'currency',
            )
        }),
        ('Economic Calendar', {
            'fields': (
                'market_indicator', 'extra_attention', 'key_indicator', 'special_news'
            )
        }),
        ('Others', {
            'fields': (
                'commentary',
            )
        })
    )

    search_fields = ('date', )
    list_per_page = 20


class MarketValuationAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'date', 'cli_trend', 'bci_trend', 'market_scenario', 'money_supply'
    )

    fieldsets = (
        ('Primary', {
            'fields': (
                'date',
            )
        }),
        ('Major Economic', {
            'fields': (
                'cli_trend', 'bci_trend', 'market_scenario', 'money_supply'
            )
        }),
        ('Monetary Policy', {
            'fields': (
                'monetary_policy',
            )
        }),
    )

    search_fields = ('date', 'cli_trend', 'bci_trend', 'market_scenario', 'money_supply')
    list_per_page = 20


class MarketIndicatorAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'date', 'fund_cash_ratio', 'fear_greek_index', 'credit_balance', 'put_call_ratio',
        'investor_sentiment', 'futures_trader',
        'support_price', 'resistant_price',
    )

    fieldsets = (
        ('Primary', {
            'fields': (
                'date',
            )
        }),
        ('Major Indicators', {
            'fields': (
                'fund_cash_ratio', 'fear_greek_index', 'credit_balance', 'put_call_ratio',
                'investor_sentiment', 'futures_trader', 'confidence_index', 'ted_spread',
                'margin_debt', 'market_breadth', 'ma200day_pct', 'arms_index',
            )
        }),
        ('Market Price Range', {
            'fields': (
                'support_price', 'resistant_price',
            )
        }),
        ('Dow theory', {
            'fields': (
                'dow_phase', 'dow_movement', 'dow_ma200x50', 'dow_volume'
            )
        }),
        ('Others technical/valuation', {
            'fields': (
                'ma50_confirm', 'fair_value_trend'
            )
        })
    )

    search_fields = ('date', )
    list_per_page = 20


class IndustryOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'symbol', 'date', 'industry', 'sector',
        'index_trend', 'isolate', 'risk_diff',
        'industry_pe', 'industry_rank', 'industry_fa', 'fair_value'
    )

    fieldsets = (
        ('Primary', {
            'fields': (
                'symbol', 'date', 'sector', 'industry'
            )
        }),
        ('Industry index', {
            'fields': (
                'index_trend', 'isolate', 'risk_diff'
            )
        }),
        ('Industry analysis', {
            'fields': (
                'biz_cycle', 'cs_trend', 'structural_chg', 'life_cycle', 'competition'
            )
        }),
        ('Industry valuation', {
            'fields': (
                'industry_pe', 'industry_rank', 'industry_fa', 'fair_value'
            )
        })
    )

    search_fields = ('symbol', 'date')
    list_filter = (
        'sector', 'index_trend', 'isolate', 'risk_diff',
        'industry_pe', 'industry_rank', 'industry_fa', 'fair_value'
    )
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


class BehaviorOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'date', 'prospect_theory', 'anchoring', 'over_confidence', 'confirmation_bias',
        'self_attribution', 'hindsight_bias', 'escalation_bias', 'serious_analysis'
    )
    fieldsets = (
        ('Primary', {
            'fields': (
                'date',
            )
        }),
        ('Behavior', {
            'fields': (
                'prospect_theory', 'belief_perseverance', 'anchoring', 'over_confidence',
                'confirmation_bias', 'self_attribution', 'hindsight_bias', 'noise_trading',
                'escalation_bias', 'serious_analysis'
            )
        }),
    )

    search_fields = ('date', )
    list_filter = ('prospect_theory', 'belief_perseverance', 'anchoring', 'over_confidence',
                   'confirmation_bias', 'self_attribution', 'hindsight_bias', 'escalation_bias',
                   'serious_analysis')
    list_per_page = 20


class FundamentalOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'symbol', 'date', 'ownership_activity', 'insider_trade', 'guru_trade', 'short_interest',
        'mean_rank', 'target_price_mean', 'earning_surprise', 'valuation',
    )
    fieldsets = (
        ('Primary', {
            'fields': (
                'symbol', 'date'
            )
        }),
        ('Ownership', {
            'fields': (
                'ownership_activity', 'insider_trade', 'guru_trade', 'short_interest',
            )
        }),
        ('Rank & Target Price', {
            'fields': (
                'mean_rank', 'target_price_max', 'target_price_mean', 'target_price_min',
            )
        }),
        ('Fundamental', {
            'fields': (
                'earning_surprise', 'earning_grow', 'dividend_grow',
                'dcf_value', 'pe_ratio_trend', 'div_yield_trend', 'valuation',
            )
        }),
    )

    search_fields = ('symbol', 'date')
    list_filter = (
        'ownership_activity', 'insider_trade', 'guru_trade', 'short_interest',
        'earning_surprise', 'earning_grow', 'dividend_grow',
        'pe_ratio_trend', 'div_yield_trend', 'valuation',

    )
    list_per_page = 20


class WeekdayOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'symbol', 'date', 'close_price', 'new_info_impact',
        'today_iv', 'iv_rank','put_call_ratio',
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

admin.site.register(MarketMovement, MarketMovementAdmin)
admin.site.register(MarketValuation, MarketValuationAdmin)
admin.site.register(MarketIndicator, MarketIndicatorAdmin)
admin.site.register(FundamentalOpinion, FundamentalOpinionAdmin)
admin.site.register(WeekdayOpinion, WeekdayOpinionAdmin)
admin.site.register(IndustryOpinion, IndustryOpinionAdmin)
admin.site.register(PositionOpinion, PositionOpinionAdmin)
admin.site.register(CloseOpinion, CloseOpinionAdmin)
admin.site.register(BehaviorOpinion, BehaviorOpinionAdmin)


admin.site.register_view(
    'opinion/profile/link/(?P<symbol>\w+)/$',
    urlname='opinion_link', view=opinion_link
)
admin.site.register_view(
    'opinion/profile/market/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='market_profile', view=market_profile
)
admin.site.register_view(
    'opinion/profile/industry/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='industry_profile', view=industry_profile
)
admin.site.register_view(
    'opinion/profile/weekday/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='weekday_profile', view=weekday_profile
)
admin.site.register_view(
    'opinion/profile/position/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='position_profile', view=position_profile
)
admin.site.register_view(
    'opinion/profile/behavior/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='behavior_profile', view=behavior_profile
)

