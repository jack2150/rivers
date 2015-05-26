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
            tb_link=reverse('admin:csv_import', args=(self.symbol.lower(), )),
            google_link=reverse('admin:web_import', args=('google', self.symbol.lower())),
            yahoo_link=reverse('admin:web_import', args=('yahoo', self.symbol.lower())),
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

# admin model
admin.site.register(Underlying, UnderlyingAdmin)
admin.site.register(Stock, StockAdmin)
admin.site.register(OptionContract, OptionContractAdmin)

# custom admin view
admin.site.register_view(
    'data/import/web/(?P<source>\w+)/(?P<symbol>\w+)/$',
    urlname='web_import', view=web_import
)

admin.site.register_view(
    'data/import/csv/(?P<symbol>\w+)/$',
    urlname='csv_import', view=csv_import
)

admin.site.register_view(
    'data/import/daily/csv/$',
    urlname='csv_daily_import', view=csv_daily_import
)

# todo: export earnings
# todo: position spread view
