from django.contrib import admin

from base.admin import DateForm
from opinion.personal.models import BehaviorOpinion


class BehaviorOpinionAdmin(admin.ModelAdmin):
    form = DateForm

    def behavior_profile(self, obj):
        return '<a href="{link}">Analysis</a>'.format(
            link=reverse('admin:behavior_profile', kwargs={'date': obj.date.strftime('%Y-%m-%d')})
        )

    behavior_profile.allow_tags = True
    behavior_profile.short_description = ''

    list_display = (
        'date', 'prospect_theory', 'anchoring', 'over_confidence', 'confirmation_bias',
        'self_attribution', 'hindsight_bias', 'escalation_bias', 'miss_opportunity',
        'serious_analysis', 'behavior_profile'
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
                'escalation_bias', 'miss_opportunity', 'serious_analysis', 'trade_addict'
            )
        }),
        ('Note', {
            'fields': (
                'other_mistake', 'other_accurate'
            )
        }),
    )

    search_fields = ('date',)
    list_filter = ('prospect_theory', 'belief_perseverance', 'anchoring', 'over_confidence',
                   'confirmation_bias', 'self_attribution', 'hindsight_bias', 'escalation_bias',
                   'serious_analysis')
    list_per_page = 20


admin.site.register(BehaviorOpinion, BehaviorOpinionAdmin)
