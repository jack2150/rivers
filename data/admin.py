from bootstrap3_datetime.widgets import DateTimePicker
from django.contrib import admin
from pandas.tseries.offsets import BDay

from data.tb.clean.views import *
from data.tb.fillna.views import fillna_normal_h5
from data.tb.raw.views import raw_stock_h5, raw_option_h5
from data.tb.valid.views import valid_option_h5
from data.event.views import html_event_import
from data.web.views import web_stock_h5, web_treasury_h5
from data.models import *
from data.views import *


class UnderlyingForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}),
        initial=pd.datetime.strptime('2009-01-01', '%Y-%m-%d')
    )
    stop_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}),
        initial=pd.Timestamp('%s%02d%02d' % (
            pd.datetime.today().year, pd.datetime.today().month, 1
        )) - BDay(1)
    )


class UnderlyingAdmin(admin.ModelAdmin):
    form = UnderlyingForm

    def data_manage(self):
        return "<a href='{link}'>Manage</a>".format(
            link=reverse('admin:manage_underlying', kwargs={'symbol': self.symbol.lower()})
        )

    data_manage.short_description = ''
    data_manage.allow_tags = True

    list_display = (
        'symbol', 'start_date', 'stop_date', 'option', 'final', data_manage
    )

    fieldsets = (
        ('Primary Fields', {
            'fields': (
                'symbol', 'start_date', 'stop_date',
                'option', 'final',
                'missing', 'log'
            )
        }),
    )

    search_fields = ('symbol', 'start', 'stop')
    list_per_page = 20


class SplitHistoryForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


class SplitHistoryAdmin(admin.ModelAdmin):
    form = SplitHistoryForm

    list_display = (
        'symbol', 'date', 'fraction'
    )

    fieldsets = (
        ('Primary Fields', {
            'fields': (
                'symbol', 'date', 'fraction'
            )
        }),
    )

    search_fields = ('symbol', 'date', 'fraction')
    list_per_page = 20


class TreasuryForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )
    stop_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


class TreasuryAdmin(admin.ModelAdmin):
    form = TreasuryForm
    list_display = ('time_period', 'start_date', 'stop_date', 'unit',
                    'multiplier', 'currency', 'unique_identifier')
    fieldsets = (
        ('Primary Fields', {
            'fields': ('start_date', 'stop_date', 'series_description', 'unit',
                       'multiplier', 'currency', 'unique_identifier', 'time_period')
        }),
    )

    search_fields = ('start_date', 'stop_date', 'series_description', 'time_period')

    list_per_page = 20
    ordering = ()

    def has_add_permission(self, request):
        return False


# admin model
admin.site.register(Underlying, UnderlyingAdmin)
admin.site.register(SplitHistory, SplitHistoryAdmin)
admin.site.register(Treasury, TreasuryAdmin)

# manage underlying
admin.site.register_view(
    'data/underlying/manage/(?P<symbol>\w+)/$',
    urlname='manage_underlying', view=manage_underlying
)


# truncate symbol
admin.site.register_view(
    'data/underlying/truncate/(?P<symbol>\w+)/$',
    urlname='truncate_symbol', view=truncate_symbol
)

# set updated
admin.site.register_view(
    'data/underlying/set/(?P<symbol>\w+)/(?P<action>\w+)/$',
    urlname='set_underlying', view=set_underlying
)

# csv h5 stock and option
admin.site.register_view(
    'data/h5/import/raw/stock/(?P<symbol>\w+)/$',
    urlname='raw_stock_h5', view=raw_stock_h5
)
admin.site.register_view(
    'data/h5/import/raw/option/(?P<symbol>\w+)/$',
    urlname='raw_option_h5', view=raw_option_h5
)
admin.site.register_view(
    'data/h5/import/valid/option/(?P<symbol>\w+)/$',
    urlname='valid_option_h5', view=valid_option_h5
)
admin.site.register_view(
    'data/h5/import/clean/normal/(?P<symbol>\w+)/$',
    urlname='clean_normal_h5', view=clean_normal_h5
)
admin.site.register_view(
    'data/h5/import/clean/split_new/(?P<symbol>\w+)/$',
    urlname='clean_split_new_h5', view=clean_split_new_h5
)
admin.site.register_view(
    'data/h5/import/clean/split_old/(?P<symbol>\w+)/$',
    urlname='clean_split_old_h5', view=clean_split_old_h5
)
admin.site.register_view(
    'data/h5/import/fillna/normal/(?P<symbol>\w+)/$',
    urlname='fillna_normal_h5', view=fillna_normal_h5
)

# web h5 stock
admin.site.register_view(
    'data/h5/import/web/(?P<source>\w+)/(?P<symbol>\w+)/$',
    urlname='web_stock_h5', view=web_stock_h5
)
admin.site.register_view(
    'data/h5/import/treasury/$',
    urlname='web_treasury_h5', view=web_treasury_h5
)

# dividend and earning
admin.site.register_view(
    'data/h5/import/event/(?P<symbol>\w+)/$',
    urlname='html_event_import', view=html_event_import
)
