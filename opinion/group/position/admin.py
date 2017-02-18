from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.contrib import admin
from django.db import models
from django.forms import Textarea

from base.admin import DateForm
from opinion.group.position.models import PortfolioReview, PositionEnter, \
    PositionHold, PositionExit, PositionReview, PositionIdea, PositionDecision, PositionComment
from opinion.group.position.views import weekday_profile, position_profile
from opinion.group.report.admin import OpinionAdmin
from statement.position.views import get_position_review


class PositionCommentInline(admin.TabularInline):
    model = PositionComment


class PortfolioReviewAdmin(admin.ModelAdmin):
    inlines = [PositionCommentInline, ]

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


class PositionIdeaAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 6, 'cols': 30})},
    }

    list_display = (
        'report', 'direction', 'target_price'
    )
    fieldsets = (
        ('TradeIdea', {'fields': (
            'report', 'direction', 'trade_idea', 'kill_it', 'target_price'
        )}),
    )

    search_fields = ('report__symbol', 'report__date', 'trade_idea', 'kill_it')
    list_filter = ('direction',)
    readonly_fields = ('report',)
    list_per_page = 20


class PositionEnterAdmin(OpinionAdmin):
    list_display = (
        'report', 'price_movement', 'event_trade',
        'risk_profile', 'bp_effect', 'max_profit', 'max_loss', 'size',
        'strategy', 'spread', 'optionable',
    )
    fieldsets = (
        ('Primary', {
            'fields': (
                'report',
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
        'report__symbol', 'report__date', 'strategy', 'enter_date', 'exit_date',
    )
    list_filter = (
        'price_movement', 'event_trade', 'risk_profile', 'spread',
        'optionable', 'event_period',
    )
    readonly_fields = ('report', )
    list_per_page = 20


class PositionExitAdmin(admin.ModelAdmin):
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


class PositionHoldAdmin(admin.ModelAdmin):
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


class PositionReviewAdmin(admin.ModelAdmin):
    list_display = ('position', 'date', 'strategy_test', 'target_price',
                    'market_review', 'complete_focus', 'mistake_trade')

    fieldsets = (
        ('Foreign Keys', {
            'fields': ('position',)
        }),
        ('Primary Fields', {
            'fields': ('date', 'description')
        }),
        ('Enter comment', {
            'fields': (
                'strategy_test', 'short_period', 'over_confidence', 'unknown_trade',
                'target_price', 'market_review', 'feel_lucky', 'wrong_timing',
                'well_backtest', 'valid_strategy', 'high_chance', 'chase_news',
                'deep_analysis', 'unaware_event', 'poor_estimate'
            )
        }),
        ('Holding comment', {
            'fields': (
                'keep_update', 'unaware_news', 'unaware_eco', 'unaware_stat',
                'hold_loser', 'wrong_wait', 'miss_profit', 'greed_wait'
            )
        }),
        ('Exit comment', {
            'fields': (
                'afraid_loss', 'luck_factor', 'news_effect', 'sold_early',
                'fear_factor', 'complete_focus', 'mistake_trade'
            )
        })
    )

    search_fields = ('position__name', 'position__spread', 'description')
    list_per_page = 20

    readonly_fields = ('position',)

    def has_add_permission(self, request):
        return False


class PositionDecisionAdmin(OpinionAdmin):
    list_display = (
        'report', 'period', 'action', 'desc',
    )
    fieldsets = (
        ('Primary', {
            'fields': (
                'report',
            )
        }),
        ('Decision', {
            'fields': (
                'period', 'action', 'desc', 'dec_desc', 'adv_desc'
            )
        }),
    )

    search_fields = ('report__symbol', 'report__date', 'desc', 'dec_desc', 'adv_desc')
    list_filter = ('period', 'action')
    readonly_fields = ('report', )
    list_per_page = 20


admin.site.register(PortfolioReview, PortfolioReviewAdmin)
admin.site.register(PositionIdea, PositionIdeaAdmin)
admin.site.register(PositionEnter, PositionEnterAdmin)
admin.site.register(PositionHold, PositionHoldAdmin)  # not used
admin.site.register(PositionExit, PositionExitAdmin)
admin.site.register(PositionReview, PositionReviewAdmin)
admin.site.register(PositionDecision, PositionDecisionAdmin)


admin.site.register_view(
    'opinion/profile/weekday/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='weekday_profile', view=weekday_profile
)
admin.site.register_view(
    'opinion/profile/position/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='position_profile', view=position_profile
)
admin.site.register_view(
    'opinion/position/review/(?P<position_id>\d+)/$',
    urlname='get_position_review', view=get_position_review
)
