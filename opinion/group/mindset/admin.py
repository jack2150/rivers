from django.contrib import admin
from django.core.urlresolvers import reverse
from opinion.group.mindset.models import MindsetBehavior, MindsetLossHold, \
    MindsetLossExcuse, MindsetNote


class MindsetNoteAdmin(admin.ModelAdmin):
    #

    list_display = (
        'note', 'date', 'category'
    )
    fieldsets = (
        ('Primary', {'fields': ('date', 'category', 'note', 'explain')}),
    )

    search_fields = ('date', 'note')
    list_filter = ('category',)
    list_per_page = 20


class MindsetBehaviorAdmin(admin.ModelAdmin):
    #

    def behavior_profile(self, obj):
        return '<a href="{link}">Analysis</a>'.format(
            link=reverse('admin:behavior_profile', kwargs={'date': obj.date.strftime('%Y-%m-%d')})
        )

    behavior_profile.allow_tags = True
    behavior_profile.short_description = ''

    list_display = (
        'date', 'over_confident', 'size_matter', 'noise_news',
        'confirm_bias', 'conservatism_bias', 'decision_time',
    )
    fieldsets = (
        ('Primary', {
            'fields': (
                'date', 'over_confident', 'size_matter', 'noise_news',
                'confirm_bias', 'conservatism_bias'
            )
        }),
        ('Common behavior', {
            'fields': (
                'emotion_think', 'trade_control', 'bad_prepare',
                'listen_because', 'prove_wrong', 'attention_blind', 'hold_power',
                'crown_pick', 'not_contrarian', 'stick_yourself', 'loss_aversion',
                'quo_bias', 'no_process', 'shortcut', 'outcome_bias',
                'self_attribute', 'hindsight_bias', 'escalation_bias', 'miss_opportunity',
                'trade_addict',
            )
        }),
        ('Extra note', {
            'fields': (
                'decision_time', 'other_mistake', 'other_accurate'
            )
        }),
    )

    search_fields = ('date', 'other_mistake', 'other_accurate')
    list_filter = ('decision_time',)
    list_per_page = 20


class MindsetLossHoldAdmin(admin.ModelAdmin):
    #

    list_display = (
        'symbol', 'date', 'avoid_now', 'take_loss'
    )
    fieldsets = (
        ('Primary', {
            'fields': (
                'symbol', 'date',
            )
        }),
        ('Admit', {
            'fields': (
                'wrong_admit', 'bad_analysis', 'good_luck', 'lazy_update'
            )
        }),
        ('Reason', {
            'fields': (
                'loss_more', 'irrational', 'new_highlow', 'valid_reverse'
            )
        }),
        ('Action', {
            'fields': (
                'avoid_now', 'take_loss'
            )
        }),
    )

    search_fields = ('date', )
    list_filter = ('avoid_now', 'take_loss')
    list_per_page = 20


class MindsetLossExcuseAdmin(admin.ModelAdmin):
    #

    list_display = (
        'symbol', 'date', 'only_if', 'outside_occur', 'almost_right', 'still_come',
        'single_predict', 'out_trouble', 'response_now'
    )
    fieldsets = (
        ('Primary', {
            'fields': (
                'symbol', 'date',
            )
        }),
        ('Excuse', {
            'fields': (
                'only_if', 'outside_occur', 'almost_right', 'still_come',
                'single_predict', 'out_trouble', 'response_now'
            )
        })
    )

    search_fields = ('date',)
    list_filter = ('out_trouble', 'response_now')
    list_per_page = 20


admin.site.register(MindsetNote, MindsetNoteAdmin)
admin.site.register(MindsetBehavior, MindsetBehaviorAdmin)
admin.site.register(MindsetLossHold, MindsetLossHoldAdmin)
admin.site.register(MindsetLossExcuse, MindsetLossExcuseAdmin)
