from bootstrap3_datetime.widgets import DateTimePicker
from django.contrib import admin

from data.plugin.fillna.views import fillna_option
from data.plugin.clean.views import *
from data.plugin.csv.views import *
from data.plugin.raw.views import *
from data.views import *


class UnderlyingForm(forms.ModelForm):
    start = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}),
        initial=pd.datetime.strptime('2009-01-01', '%Y-%m-%d')
    )
    stop = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}),
        initial=pd.Timestamp('%s%02d%02d' % (
            pd.datetime.today().year, pd.datetime.today().month, 1
        )) - BDay(1)
    )


class UnderlyingAdmin(admin.ModelAdmin):
    form = UnderlyingForm

    def data_manage(self):
        href = """
        <div class="dropdown">
          <button class="btn btn-default btn-xs dropdown-toggle" type="button"
            id="dropdownMenu1" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">
            Manage
            <span class="caret"></span>
          </button>
          <ul class="dropdown-menu" aria-labelledby="dropdownMenu1">
            <li><a href="{stock_link}">Csv import stock</a></li>
            <li><a href="{option_link}">Csv import options</a></li>
            <li><a href="{google_link}">Web import google</a></li>
            <li><a href="{yahoo_link}">Web import yahoo</a></li>
            <li class="divider"></li>
            <li><a href="{event_import}">Event import</a></li>
            <li class="divider"></li>
            <li><a href="{truncate_link}">Truncate data</a></li>
          </ul>
        </div>
        """
        symbol = self.symbol.lower()
        return href.format(
            stock_link=reverse('admin:csv_stock_h5', kwargs={'symbol': symbol}),
            option_link=reverse('admin:csv_option_h5', kwargs={'symbol': symbol}),
            google_link=reverse('admin:web_stock_h5', args=('google', symbol)),
            yahoo_link=reverse('admin:web_stock_h5', args=('yahoo', symbol)),
            event_import=reverse('admin:html_event_import', kwargs={'symbol': symbol}),
            truncate_link=reverse('admin:truncate_symbol', kwargs={'symbol': symbol})
        )

    data_manage.short_description = ''
    data_manage.allow_tags = True

    list_display = (
        'symbol', 'start', 'stop', 'thinkback', 'contract', 'option',
        'google', 'yahoo', 'earning', 'dividend', 'updated', 'optionable',
        data_manage
    )

    fieldsets = (
        ('Primary Fields', {
            'fields': (
                'symbol', 'start', 'stop',
                'thinkback', 'contract', 'option',
                'google', 'yahoo',
                'earning', 'dividend',
                'updated', 'optionable', 'missing'
            )
        }),
    )

    readonly_fields = ('thinkback', 'google', 'yahoo',
                       'contract', 'option', 'earning', 'dividend',)

    search_fields = ('symbol', 'start', 'stop')
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
admin.site.register(Treasury, TreasuryAdmin)

# admin view
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
    'data/h5/import/csv/stock/(?P<symbol>\w+)/$',
    urlname='csv_stock_h5', view=csv_stock_h5
)
admin.site.register_view(
    'data/h5/import/csv/option/(?P<symbol>\w+)/$',
    urlname='csv_option_h5', view=csv_option_h5
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


# clean option data
admin.site.register_view(
    'data/h5/clean/csv/option/(?P<symbol>\w+)/(?P<core>\d+)/$',
    urlname='clean_option', view=clean_option
)

admin.site.register_view(
    'data/h5/fillna/csv/option/(?P<symbol>\w+)/$',
    urlname='fillna_option', view=fillna_option
)

admin.site.register_view(
    'data/h5/import/csv/option2/(?P<symbol>\w+)/$',
    urlname='csv_option_h5x', view=csv_option_h5x
)
