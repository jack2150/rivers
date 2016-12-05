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
        'name', 'date', 'nav_start', 'nav_mark', 'nav_fee', 'nav_value', ib_import
    )
    fieldsets = (
        ('Primary', {'fields': ('name', 'date')}),
        ('Net Asset Value', {'fields': ('nav_start', 'nav_mark', 'nav_fee', 'nav_value')}),

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

    search_fields = ('statement__name__name', )
    list_filter = ('asset', )
    list_per_page = 20


class IBMarkToMarketAdmin(admin.ModelAdmin):
    list_display = (
        'symbol', 'statement', 'qty0', 'qty1', 'price0', 'price1', 'pl_total'
    )
    fieldsets = (
        ('Foreign', {'fields': ('statement',)}),
        ('Position', {'fields': (
            'symbol', 'qty0', 'qty1', 'price0', 'price1',
        )}),
        ('Profit Loss', {'fields': (
            'pl_pos', 'pl_trans', 'pl_fee', 'pl_other', 'pl_total'
        )}),
    )

    search_fields = ('statement__name__name', 'symbol')
    list_filter = ()
    list_per_page = 20


class IBPerformanceAdmin(admin.ModelAdmin):
    list_display = (
        'symbol', 'statement', 'cost_adj', 'real_total', 'unreal_total', 'total'
    )
    fieldsets = (
        ('Foreign', {'fields': ('statement',)}),
        ('Performance', {'fields': (
            'symbol', 'cost_adj', 'total'
        )}),
        ('Realized Profit/Loss', {'fields': (
            'real_st_profit', 'real_st_loss', 'real_lt_profit', 'real_lt_loss', 'real_total',
        )}),
        ('Unrealized Profit/Loss', {'fields': (
            'unreal_st_profit', 'unreal_st_loss', 'unreal_lt_profit', 'unreal_lt_loss', 'unreal_total',
        )}),
    )

    search_fields = ('statement__name__name', 'symbol')
    list_filter = ()
    list_per_page = 20


admin.site.register(IBStatementName, IBStatementNameAdmin)
admin.site.register(IBStatement, IBStatementAdmin)
admin.site.register(IBNetAssetValue, IBNetAssetValueAdmin)
admin.site.register(IBMarkToMarket, IBMarkToMarketAdmin)
admin.site.register(IBPerformance, IBPerformanceAdmin)

admin.site.register_view(
    'broker/ib/date/(?P<broker_id>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
    urlname='ib_statement_import', view=ib_statement_import
)
admin.site.register_view(
    'broker/ib/import/(?P<ib_path>\w+)/$',
    urlname='ib_statement_imports', view=ib_statement_imports
)
