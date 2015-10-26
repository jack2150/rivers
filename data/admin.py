from bootstrap3_datetime.widgets import DateTimePicker
from django.contrib import admin
from pandas.tseries.offsets import BDay
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
        #href = '<a href="{truncate_link}">Truncate</a>'
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
            <li><a href="{earning_import}">Earning import</a></li>
            <li><a href="{dividend_import}">Dividend import</a></li>
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
            earning_import=reverse('admin:html_event_import', kwargs={
                'event': 'earning', 'symbol': symbol
            }),
            dividend_import=reverse('admin:html_event_import', kwargs={
                'event': 'dividend', 'symbol': symbol
            }),
            truncate_link=reverse('admin:truncate_symbol', kwargs={'symbol': symbol})
        )

    data_manage.short_description = ''
    data_manage.allow_tags = True

    list_display = (
        'symbol', 'start', 'stop', 'thinkback', 'contract', 'option',
        'google', 'yahoo', 'earning', 'dividend','updated', 'optionable',
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
    'data/thinkback/truncate/(?P<symbol>\w+)/$',
    urlname='truncate_symbol', view=truncate_symbol
)

# set updated
admin.site.register_view(
    'data/underlying/set/(?P<symbol>\w+)/(?P<action>\w+)/$',
    urlname='set_underlying', view=set_underlying
)

# csv h5 stock and option
admin.site.register_view(
    'data/h5/quote/csv/stock/(?P<symbol>\w+)/$',
    urlname='csv_stock_h5', view=csv_stock_h5
)
admin.site.register_view(
    'data/h5/quote/csv/option/(?P<symbol>\w+)/$',
    urlname='csv_option_h5', view=csv_option_h5
)

# web h5 stock
admin.site.register_view(
    'data/h5/quote/web/(?P<source>\w+)/(?P<symbol>\w+)/$',
    urlname='web_stock_h5', view=web_stock_h5
)
admin.site.register_view(
    'data/h5/treasury/$',
    urlname='web_treasury_h5', view=web_treasury_h5
)

# dividend and earning
admin.site.register_view(
    'data/h5/(?P<event>\w+)/(?P<symbol>\w+)/$',
    urlname='html_event_import', view=html_event_import
)
