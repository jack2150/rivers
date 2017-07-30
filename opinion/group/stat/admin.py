from django.contrib import admin
from django.core.urlresolvers import reverse

from opinion.group.stat.models import StatPrice


class StatPriceAdmin(admin.ModelAdmin):
    def link(self, obj):
        return '{link}'.format(
            link='<a href="%s" target="_blank">Basic</a>' %
                 reverse('report_statprice', kwargs={'symbol': obj.symbol.lower()})
        )

    link.allow_tags = True

    list_display = (
        'symbol', 'date', 'move', 'rare', 'bday5d', 'bday20d', 'bday60d', 'opportunity', 'link'
    )
    fieldsets = (
        ('Primary', {'fields': ('symbol', 'date')}),
        ('Price statistics', {'fields': (
            'move', 'rare', 'bday5d', 'bday20d', 'bday60d', 'opportunity'
        )}),
    )

    search_fields = (
        'symbol',
    )
    list_filter = ('rare', 'opportunity')
    ordering = ('-date',)

    list_per_page = 20


admin.site.register(StatPrice, StatPriceAdmin)
