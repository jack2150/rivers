from django.contrib import admin
from opinion.group.quest.models import QuestLine, QuestPart


class QuestPartInline(admin.TabularInline):
    model = QuestPart
    extra = 0


class QuestLineAdmin(admin.ModelAdmin):
    inlines = [QuestPartInline]

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


admin.site.register(QuestLine, QuestLineAdmin)


