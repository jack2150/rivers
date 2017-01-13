from bootstrap3_datetime.widgets import DateTimePicker
from django.contrib import admin
from pandas.tseries.offsets import BDay

from data.option.day_iv.views import calc_day_iv
from data.tb.clean.views import *
from data.tb.fillna.views import fillna_missing_h5
from data.tb.final.views import merge_final_h5, remove_clean_h5, import_option_h5, import_weekday_h5
from data.tb.raw.views import raw_stock_h5, raw_option_h5
from data.tb.raw2.views import raw2_option_h5
from data.tb.revalid.views import valid_clean_h5
from data.tb.valid.views import valid_option_h5
from data.event.views import html_event_import
from data.ticker.views import web_yahoo_minute_data
from data.web.views import web_stock_h5, web_treasury_h5
from data.models import *
from data.views import *


class UnderlyingAdmin(admin.ModelAdmin):
    def data_manage(self):
        return "<a href='{link}'>Manage</a>".format(
            link=reverse('admin:manage_underlying', kwargs={'symbol': self.symbol.lower()})
        )

    data_manage.short_description = ''
    data_manage.allow_tags = True

    # noinspection PyMethodMayBeStatic
    def toggle_final(self, request, queryset):
        for q in queryset.all():
            q.final = not q.final
            q.save()

    toggle_final.short_description = "Toggle underlying final"
    actions = [toggle_final]

    list_display = (
        'symbol', 'company', 'start_date', 'stop_date',
        'final', 'enable', 'optionable', 'shortable', data_manage
    )

    fieldsets = (
        ('Primary Fields', {
            'fields': (
                'symbol', 'start_date', 'stop_date', 'optionable', 'shortable', 'final'
            ),
        }),
        ('Underlying Fields', {
            'fields': (
                'company', 'sector', 'industry', 'exchange',
                'market_cap', 'country', 'activity', 'classify',
            ),
        }),
        ('Data Fields', {
            'fields': (
                'missing', 'log', 'google_symbol', 'yahoo_symbol'
            ),
        }),
    )

    search_fields = ('symbol', 'company', 'sector', 'industry')
    list_filter = (
        'enable', 'final', 'optionable', 'shortable',
        'exchange', 'country', 'activity', 'classify',
    )
    list_per_page = 20


class SplitHistoryAdmin(admin.ModelAdmin):
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


class TreasuryAdmin(admin.ModelAdmin):
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
admin.site.register_view(
    'data/underlying/renew_season/$', urlname='renew_season', view=renew_season
)

# update underlying
admin.site.register_view(
    'data/underlying/update/(?P<symbol>\w+)/$',
    urlname='update_underlying', view=update_underlying
)
admin.site.register_view(
    'data/splithistory/insert/(?P<symbol>\w+)/$',
    urlname='add_split_history', view=add_split_history
)

# csv h5 stock and option
admin.site.register_view(
    'data/h5/import/stock/(?P<symbol>\w+)/$', urlname='raw_stock_h5', view=raw_stock_h5
)
admin.site.register_view(
    'data/h5/import/raw/option/(?P<symbol>\w+)/$', urlname='raw_option_h5', view=raw_option_h5
)
admin.site.register_view(
    'data/h5/import/raw2/option/(?P<symbol>\w+)/$', urlname='raw2_option_h5', view=raw2_option_h5
)
admin.site.register_view(
    'data/h5/process/valid/option/(?P<symbol>\w+)/$',
    urlname='valid_option_h5', view=valid_option_h5
)
admin.site.register_view(
    'data/h5/process/clean/option/(?P<symbol>\w+)/(?P<name>\w+)/$',
    urlname='clean_valid_h5', view=clean_valid_h5
)
admin.site.register_view(
    'data/h5/process/valid/clean/(?P<symbol>\w+)/$',
    urlname='valid_clean_h5', view=valid_clean_h5
)
admin.site.register_view(
    'data/h5/process/fillna/normal/(?P<symbol>\w+)/(?P<name>\w+)/$',
    urlname='fillna_missing_h5', view=fillna_missing_h5
)
admin.site.register_view(
    'data/h5/process/merge/final/(?P<symbol>\w+)/$',
    urlname='merge_final_h5', view=merge_final_h5
)
admin.site.register_view(
    'data/h5/remove/temp/(?P<symbol>\w+)/$',
    urlname='remove_clean_h5', view=remove_clean_h5
)
admin.site.register_view(
    'data/h5/import/option/(?P<symbol>\w+)/$',
    urlname='import_option_h5', view=import_option_h5
)
admin.site.register_view(
    'data/h5/import/weekday/(?P<symbol>\w+)/$',
    urlname='import_weekday_h5', view=import_weekday_h5
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
admin.site.register_view(
    'data/h5/raw_df/(?P<symbol>\w+)/(?P<source>\w+)/$',
    urlname='stock_raw', view=stock_raw
)

# dividend and earning
admin.site.register_view(
    'data/h5/import/event/(?P<symbol>\w+)/$',
    urlname='html_event_import', view=html_event_import
)
admin.site.register_view(
    'data/h5/raw_event/(?P<symbol>\w+)/(?P<event>\w+)/$',
    urlname='event_raw', view=event_raw
)

# calc iv
admin.site.register_view(
    'data/h5/calc/iv/(?P<symbol>\w+)/(?P<insert>\d)$',
    urlname='calc_day_iv', view=calc_day_iv
)

# minute ticker
admin.site.register_view(
    'ticker/yahoo/minute/download/(?P<symbol>\w+)/$',
    urlname='web_yahoo_minute_data', view=web_yahoo_minute_data
)

