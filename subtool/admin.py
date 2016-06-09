import logging
import pandas as pd
from django import forms
from django.contrib import admin
from bootstrap3_datetime.widgets import DateTimePicker
from django.core.urlresolvers import reverse

from rivers.settings import QUOTE_DIR
from subtool.live.excel_rtd.views import excel_rtd_create
from subtool.models import OptionTimeSale
from subtool.option.timesale.views import timesale_report_view, timesale_insert_view

logger = logging.getLogger('views')


class DateForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


class OptionTimeSaleAdmin(admin.ModelAdmin):
    form = DateForm  # enable bootstrap datetime js

    def report(self):
        return '<a href="{link}">Report</a>'.format(
            link=reverse(
                'admin:timesale_report_view',
                kwargs={'symbol': self.symbol.lower(), 'date': self.date.strftime('%Y-%m-%d')}
            )
        )

    report.allow_tags = True

    list_display = ['symbol', 'date', report]
    fieldsets = (
        ('Primary Fields', {
            'fields': (
                'symbol', 'date', 'extra_field',
            )
        }),
    )
    search_fields = ('symbol', 'date')
    list_per_page = 20

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        # Disable delete
        actions = super(OptionTimeSaleAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def delete_report(self, request, queryset):
        for q in queryset.all():
            timesale = OptionTimeSale.objects.get(id=q.id)
            logger.info('OptionTimeSale: %s %s' % (
                timesale.symbol, timesale.date.strftime('%Y-%m-%d')
            ))

            db = pd.HDFStore(QUOTE_DIR)
            path = '/option/%s/final/timesale' % timesale.symbol.lower()
            try:
                df_timesale = db.select(path, 'date == %r' % pd.to_datetime(timesale.date))
                logger.info('df_timesale remove: %d' % len(df_timesale))
            except KeyError:
                pass

            try:
                db.remove(path, where='date == %r' % pd.to_datetime(timesale.date))
            except NotImplementedError:
                db.remove(path)
            except KeyError:
                pass

            db.close()

        queryset.delete()

    delete_report.short_description = "Delete option time sale report"
    actions = [delete_report]


admin.site.register(OptionTimeSale, OptionTimeSaleAdmin)

admin.site.register_view(
    'subtool/optiontimesale/input', urlname='timesale_insert_view', view=timesale_insert_view
)
admin.site.register_view(
    'subtool/optiontimesale/summary/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='timesale_report_view', view=timesale_report_view
)
admin.site.register_view(
    'subtool/live/excel_rtd/create', urlname='excel_rtd_create', view=excel_rtd_create
)









