from django.contrib import admin

from base.admin import StartStopForm, DateForm
from opinion.plan.models import TradingPlan, TradeIdea, TradeNote, TradingQuest
from opinion.plan.views import trade_note


class TradingPlanAdmin(admin.ModelAdmin):
    form = StartStopForm

    list_display = (
        'name', 'start', 'stop', 'goal', 'profit_target', 'loss_drawdown',
        'plan_result', 'plan_return', 'active'
    )
    fieldsets = (
        ('Primary', {'fields': ('name', 'start', 'stop', 'goal', 'active')}),
        ('Portfolio', {'fields': ('profit_target', 'loss_drawdown')}),
        ('Position', {'fields': ('pos_size0', 'pos_size1', 'pos_size2', 'holding_num',)}),
        ('Risk ', {'fields': ('risk_profile', 'max_loss', 'max_profit',)}),
        ('Holding period', {'fields': ('holding_period', 'by_term', 'term_value',)}),
        ('Instrument', {'fields': ('instrument', 'custom_item', 'symbols')}),
        ('Trade frequency', {'fields': ('trade_enter', 'trade_exit', 'trade_adjust',)}),
        ('Note', {'fields': ('description',)}),
        ('Result', {'fields': ('plan_result', 'plan_return', 'advantage', 'weakness', 'conclusion')}),
    )

    search_fields = ('name', 'start', 'stop', 'description', 'conclusion')
    list_filter = ('goal', 'active', 'risk_profile', 'holding_period', 'by_term', 'instrument',
                   'trade_enter', 'trade_exit', 'trade_adjust', 'plan_result')

    list_per_page = 20


class TradingQuestAdmin(admin.ModelAdmin):
    form = StartStopForm

    list_display = (
        'trading_plan', 'name', 'category', 'start', 'stop', 'achievement'
    )
    fieldsets = (
        ('Primary', {'fields': ('trading_plan',)}),
        ('Portfolio', {'fields': ('name', 'category', 'start', 'stop', 'description')}),
        ('Result', {'fields': ('achievement', 'experience')}),
    )

    search_fields = ('trading_plan__name', 'name', 'description', 'experience')
    list_filter = ('trading_plan__name', 'category', 'achievement',)

    list_per_page = 20


class TradeIdeaAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'symbol', 'date', 'direction', 'target_price'
    )
    fieldsets = (
        ('Primary', {'fields': ('symbol', 'date')}),
        ('Idea', {'fields': ('direction', 'trade_idea', 'target_price')}),
    )

    search_fields = ('date', 'symbol', 'trade_idea')
    list_filter = ('direction',)
    list_per_page = 20


class TradeNoteAdmin(admin.ModelAdmin):
    form = DateForm

    list_display = (
        'date', 'note'
    )
    fieldsets = (
        ('Primary', {'fields': ('date', 'note', 'explain')}),
    )

    search_fields = ('date', 'note')
    list_per_page = 20


admin.site.register(TradingPlan, TradingPlanAdmin)
admin.site.register(TradingQuest, TradingQuestAdmin)
admin.site.register(TradeIdea, TradeIdeaAdmin)
admin.site.register(TradeNote, TradeNoteAdmin)

admin.site.register_view(
    'opinion/profile/tradenote/$', urlname='trade_note', view=trade_note
)
