from django.contrib import admin
from django.core.urlresolvers import reverse
from base.admin import StartStopForm, DateForm
from broker.ib.models import *
from broker.ib.views import ib_statement_import, ib_statement_imports


class IBStatementNameAdmin(admin.ModelAdmin):
    form = StartStopForm

    def ib_imports(self):
        return '<a href="{link}">Imports</a>'.format(
            link=reverse('admin:ib_statement_imports', kwargs={
                'ib_path': self.path
            })
        )

    ib_imports.short_description = ''
    ib_imports.allow_tags = True

    list_display = (
        'name', 'broker_id', 'path', 'account_type', 'customer_type', 'capability', ib_imports
    )
    fieldsets = (
        ('Primary', {'fields': ('name', 'broker_id', 'start', 'stop')}),
        ('Detail', {'fields': (
            'path', 'account_type', 'customer_type', 'capability', 'description'
        )}),

    )

    search_fields = ('name', 'broker_id', 'description')
    list_filter = ('account_type', 'customer_type')
    list_per_page = 20


class IBStatementAdmin(admin.ModelAdmin):
    form = DateForm

    def ib_import(self):
        return '<a href="{link}">Import</a>'.format(
            link=reverse('admin:ib_statement_import', kwargs={
                'broker_id': self.name.broker_id, 'date': self.date.strftime('%Y-%m-%d')
            })
        )
    ib_import.short_description = ''
    ib_import.allow_tags = True

    list_display = (
        'name', 'date', ib_import
    )
    fieldsets = (
        ('Primary', {'fields': ('name', 'date')}),

    )

    search_fields = ('name__name', 'date')
    list_filter = ('name', 'name__name',)
    list_per_page = 20


class IBNetAssetValueAdmin(admin.ModelAdmin):
    list_display = (
        'statement', 'asset', 'total0', 'total1', 'short_sum', 'long_sum', 'change'
    )
    fieldsets = (
        ('Foreign', {'fields': ('statement', )}),
        ('Detail', {'fields': (
            'asset', 'total0', 'total1', 'short_sum', 'long_sum', 'change'
        )}),
    )

    search_fields = ('name__name', )
    list_filter = ('asset', )
    list_per_page = 20


admin.site.register(IBStatementName, IBStatementNameAdmin)
admin.site.register(IBStatement, IBStatementAdmin)
admin.site.register(IBNetAssetValue, IBNetAssetValueAdmin)

admin.site.register_view(
    'broker/ib/date/(?P<broker_id>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='ib_statement_import', view=ib_statement_import
)
admin.site.register_view(
    'broker/ib/import/(?P<ib_path>\w+)/$',
    urlname='ib_statement_imports', view=ib_statement_imports
)

