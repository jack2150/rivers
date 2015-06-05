from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.contrib import admin
from django.core.urlresolvers import reverse
from data.views import *
import pandas as pd


class UnderlyingForm(forms.ModelForm):
    start = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}),
        initial=pd.datetime.strptime('2009-01-01', '%Y-%m-%d')
    )
    stop = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False}),
        initial=pd.datetime.today()
    )


class UnderlyingAdmin(admin.ModelAdmin):
    form = UnderlyingForm

    def data_import(self):
        href = '<a href="{tb_link}">ThinkBack</a> | ' \
               '<a href="{google_link}">Google</a> | ' \
               '<a href="{yahoo_link}">Yahoo</a>'

        return href.format(
            tb_link=reverse('admin:csv_quote_import', args=(self.symbol.lower(), )),
            google_link=reverse('admin:web_quote_import', args=('google', self.symbol.lower())),
            yahoo_link=reverse('admin:web_quote_import', args=('yahoo', self.symbol.lower())),
        )

    data_import.short_description = 'Import from Source'
    data_import.allow_tags = True

    list_display = ('symbol', 'start', 'stop', 'thinkback', 'google', 'yahoo', data_import)

    fieldsets = (
        ('Primary Fields', {
            'fields': ('symbol', 'start', 'stop', 'thinkback', 'google', 'yahoo')
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
    list_display = ('symbol', 'ex_month', 'ex_year', 'right', 'special',
                    'strike', 'contract', 'option_code', 'others', 'source')

    fieldsets = (
        ('Primary Fields', {
            'fields': ('symbol', 'ex_month', 'ex_year', 'right', 'special',
                       'strike', 'contract', 'option_code', 'others', 'source')
        }),
    )

    search_fields = ('symbol', 'ex_month', 'ex_year', 'right', 'special',
                     'strike', 'contract', 'option_code', 'others')

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
    list_display = ('symbol', 'amount', 'announce_date', 'expire_date',
                    'record_date', 'payable_date')

    fieldsets = (
        ('Primary Fields', {
            'fields': ('symbol', 'amount', 'announce_date', 'expire_date',
                       'record_date', 'payable_date')
        }),
    )

    search_fields = ('symbol', 'amount', 'announce_date', 'expire_date',
                     'record_date', 'payable_date')

    list_per_page = 20
    ordering = ('-expire_date', )

    def has_add_permission(self, request):
        return False


class EarningForm(forms.ModelForm):
    date_est = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )

    date_act = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


class EarningAdmin(admin.ModelAdmin):
    form = EarningForm
    list_display = ('date_est', 'date_act', 'release', 'time',
                    'symbol', 'quarter', 'esp_est', 'esp_act', 'status')

    fieldsets = (
        ('Primary Fields', {
            'fields': ('date_est', 'date_act', 'release', 'time',
                       'symbol', 'quarter', 'esp_est', 'esp_act', 'status')
        }),
    )

    search_fields = ('date_est', 'release', 'symbol', 'quarter', 'status')
    list_filter = ('release', 'quarter', 'status')

    list_per_page = 20
    ordering = ('-date_est', )

    def has_add_permission(self, request):
        return False


# todo: next
class TreasuryInstrumentAdmin(admin.ModelAdmin):
    list_display = ('unique_identifier','name', 'instrument', 'maturity',
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
    'data/import/quote/csv/(?P<symbol>\w+)/$', urlname='csv_quote_import', view=csv_quote_import
)

admin.site.register_view(
    'data/import/daily/quote/$', urlname='daily_quote_import', view=daily_quote_import
)

admin.site.register_view(
    'data/import/(?P<event>\w+)/$', urlname='csv_calendar_import', view=csv_calendar_import
)

admin.site.register_view(
    'data/import/treasury/$', urlname='treasury_import', view=treasury_import
)

# todo: position spread view
# todo: manager stock direct pandas sql io
