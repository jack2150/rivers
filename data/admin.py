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
        initial=datetime.date(
            year=datetime.datetime.today().year,
            month=datetime.datetime.today().month,
            day=1
        ) - BDay(1)
    )


class UnderlyingAdmin(admin.ModelAdmin):
    form = UnderlyingForm

    def csv_import(self):
        href = '<a href="{stock_link}">Stock</a> | ' \
               '<a href="{option_link}">Options</a>'
        return href.format(
            stock_link=reverse('admin:csv_stock_import', kwargs={'symbol': self.symbol.lower()}),
            option_link=reverse('admin:csv_option_import', kwargs={'symbol': self.symbol.lower()}),
        )

    csv_import.short_description = 'Csv'
    csv_import.allow_tags = True

    def web_import(self):
        href = '<a href="{google_link}">Google</a> | ' \
               '<a href="{yahoo_link}">Yahoo</a>'

        return href.format(
            google_link=reverse('admin:web_quote_import', args=('google', self.symbol.lower())),
            yahoo_link=reverse('admin:web_quote_import', args=('yahoo', self.symbol.lower()))
        )

    web_import.short_description = 'Web'
    web_import.allow_tags = True

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
            <li><a href="{opinion_link}">Opinion link</a></li>
            <li class="divider"></li>
            <li><a href="{truncate_link}">Truncate data</a></li>
          </ul>
        </div>
        """
        symbol = self.symbol.lower()
        return href.format(
            stock_link=reverse('admin:csv_stock_import', kwargs={'symbol': symbol}),
            option_link=reverse('admin:csv_option_import', kwargs={'symbol': symbol}),
            google_link=reverse('admin:web_quote_import', args=('google', symbol)),
            yahoo_link=reverse('admin:web_quote_import', args=('yahoo', symbol)),
            earning_import=reverse('admin:event_import', kwargs={'event': 'earning', 'symbol': symbol}),
            dividend_import=reverse('admin:event_import', kwargs={'event': 'dividend', 'symbol': symbol}),
            truncate_link=reverse('admin:truncate_symbol', kwargs={'symbol': symbol}),
            opinion_link=reverse('admin:enter_opinion_links', kwargs={'symbol': symbol})
        )

    data_manage.short_description = ''
    data_manage.allow_tags = True

    list_display = (
        'symbol', 'start', 'stop', 'thinkback', 'google', 'yahoo', 'updated', 'validated',
        data_manage
    )

    fieldsets = (
        ('Primary Fields', {
            'fields': (
                'symbol', 'start', 'stop', 'thinkback', 'google', 'yahoo',
                'updated', 'validated', 'missing_dates'
            )
        }),
    )

    readonly_fields = ('thinkback', 'google', 'yahoo')

    search_fields = ('symbol', 'start', 'stop')
    list_per_page = 20


class StockForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


class StockAdmin(admin.ModelAdmin):
    form = StockForm
    list_display = ('symbol', 'date', 'open', 'high', 'low', 'close', 'source')

    fieldsets = (
        ('Foreign Keys', {
            'fields': ('underlying',)
        }),
        ('Primary Fields', {
            'fields': ('symbol', 'date', 'open', 'high', 'low', 'close', 'source')
        }),
    )

    search_fields = ('symbol', 'date', 'source')
    list_per_page = 20

    def has_add_permission(self, request):
        return False


class OptionContractAdmin(admin.ModelAdmin):
    list_display = (
        'symbol', 'ex_month', 'ex_year', 'right', 'special',
        'strike', 'name', 'option_code', 'others', 'source',
        'expire', 'code_change', 'missing'
        # 'forfeit', 'split',
    )

    fieldsets = (
        ('Primary Fields', {
            'fields': (
                'symbol', 'ex_month', 'ex_year', 'right', 'special',
                'strike', 'name', 'option_code', 'others', 'source',
                'expire', 'code_change', 'split', 'missing', 'forfeit'
            )
        }),
    )

    search_fields = ('symbol', 'ex_month', 'ex_year', 'special',
                     'strike', 'name', 'option_code', 'others')

    list_per_page = 20

    def has_add_permission(self, request):
        return False


class DividendForm(forms.ModelForm):
    announce_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )

    expire_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )

    record_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )

    payable_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


class DividendAdmin(admin.ModelAdmin):
    form = DividendForm
    list_display = ('symbol', 'year', 'quarter',
                    'announce_date', 'expire_date', 'record_date', 'payable_date',
                    'amount', 'dividend_type')

    fieldsets = (
        ('Primary Fields', {
            'fields': ('symbol', 'year', 'quarter',
                       'announce_date', 'expire_date', 'record_date', 'payable_date',
                       'amount', 'dividend_type')
        }),
    )

    search_fields = ('symbol', 'year', 'quarter', 'dividend_type')

    list_per_page = 20
    ordering = ('-expire_date', )

    def has_add_permission(self, request):
        return False


class EarningForm(forms.ModelForm):
    actual_date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


class EarningAdmin(admin.ModelAdmin):
    form = EarningForm
    list_display = ('symbol', 'actual_date', 'release', 'year', 'quarter',
                    'analysts', 'estimate_eps', 'adjusted_eps', 'gaap',
                    'high', 'low', 'actual_eps')

    fieldsets = (
        ('Primary Fields', {
            'fields': ('symbol', 'actual_date', 'release', 'year', 'quarter',
                       'analysts', 'estimate_eps', 'adjusted_eps', 'gaap',
                       'high', 'low', 'actual_eps')
        }),
    )

    search_fields = ('symbol', 'release', 'year', 'quarter')
    list_filter = ('release', 'quarter')

    list_per_page = 20
    ordering = ('-actual_date', )

    def has_add_permission(self, request):
        return False


class TreasuryInstrumentAdmin(admin.ModelAdmin):
    list_display = ('unique_identifier', 'name', 'instrument', 'maturity',
                    'unit', 'multiplier', 'currency', 'time_frame')
    fieldsets = (
        ('Primary Fields', {
            'fields': ('name', 'instrument', 'maturity', 'description',
                       'unit', 'multiplier', 'currency', 'unique_identifier',
                       'time_period', 'time_frame')
        }),
    )

    search_fields = ('name', 'instrument', 'maturity', 'description',
                     'unit', 'multiplier', 'currency', 'unique_identifier',
                     'time_period', 'time_frame')
    list_filter = ('name', 'maturity', 'unit', 'multiplier', 'time_frame')

    list_per_page = 20
    ordering = ('name', )

    def has_add_permission(self, request):
        return False


class TreasuryInterestForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


class TreasuryInterestAdmin(admin.ModelAdmin):
    form = TreasuryInterestForm
    list_display = ('treasury', 'date', 'interest')
    fieldsets = (
        ('Foreign Keys', {
            'fields': ('treasury',)
        }),
        ('Primary Fields', {
            'fields': ('date', 'interest')
        }),
    )

    search_fields = ('treasury__name', 'treasury__instrument', 'treasury__maturity',
                     'treasury__description', 'treasury__unit', 'treasury__multiplier',
                     'treasury__currency', 'treasury__unique_identifier',
                     'treasury__time_period', 'treasury__time_frame')
    list_filter = ('treasury__name', 'treasury__maturity', 'treasury__unit',
                   'treasury__multiplier', 'treasury__time_frame')

    list_per_page = 20
    ordering = ('treasury__name', '-date', )

    def has_add_permission(self, request):
        return False


# admin model
admin.site.register(Underlying, UnderlyingAdmin)
admin.site.register(Stock, StockAdmin)
admin.site.register(OptionContract, OptionContractAdmin)
admin.site.register(Dividend, DividendAdmin)
admin.site.register(Earning, EarningAdmin)
admin.site.register(TreasuryInstrument, TreasuryInstrumentAdmin)
admin.site.register(TreasuryInterest, TreasuryInterestAdmin)

# custom admin view
admin.site.register_view(
    'data/import/quote/web/(?P<source>\w+)/(?P<symbol>\w+)/$',
    urlname='web_quote_import', view=web_quote_import
)

admin.site.register_view(
    'data/import/treasury/$',
    urlname='treasury_import', view=treasury_import
)

admin.site.register_view(
    'data/thinkback/truncate/(?P<symbol>\w+)/$',
    urlname='truncate_symbol', view=truncate_symbol
)

# csv import
admin.site.register_view(
    'data/import/quote/csv/stock/(?P<symbol>\w+)/$',
    urlname='csv_stock_import', view=csv_stock_import
)

admin.site.register_view(
    'data/import/quote/csv/option/(?P<symbol>\w+)/$',
    urlname='csv_option_import', view=csv_option_import
)

# set updated
admin.site.register_view(
    'data/underlying/set/(?P<symbol>\w+)/(?P<action>\w+)/$',
    urlname='set_underlying', view=set_underlying
)

admin.site.register_view(
    'data/import/(?P<event>\w+)/(?P<symbol>\w+)/$',
    urlname='event_import', view=event_import
)

admin.site.register_view(
    'data/import/daily/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='daily_import', view=daily_import
)

