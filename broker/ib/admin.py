from django.contrib import admin
from django.core.urlresolvers import reverse
from django.forms import fields_for_model

from broker.ib.models import *
from broker.ib.views import ib_statement_import, ib_statement_imports


class IBStatementInline(admin.TabularInline):
    model = IBStatement
    extra = 0

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class IBStatementNameAdmin(admin.ModelAdmin):
    # inlines = (IBStatementInline, )

    def ib_import(self, obj):
        return '{truncate} | {imports} | {report}'.format(
            imports='<a href="%s" target="_blank">Imports</a>' % reverse(
                'ib_statement_imports', kwargs={'ib_path': obj.path}
            ),
            report='<a href="%s" target="_blank">Csv</a>' % reverse(
                'ib_statement_create_csv', kwargs={'obj_id': obj.id}
            ),
            truncate='<a href="%s" target="_blank" %s>Truncate</a>' % (
                reverse('ib_statement_truncate', kwargs={'obj_id': obj.id}),
                """
                onclick = "return confirm('Are your sure?')"
                """
            ),
        )

    ib_import.short_description = 'Statement'
    ib_import.allow_tags = True

    def pos_manage(self, obj):
        return '{create} | {remove}'.format(
            create='<a href="%s" target="_blank">Create</a>' % reverse(
                'ib_position_create', kwargs={'obj_id': obj.id}
            ),
            remove='<a href="%s" target="_blank">Remove</a>' % reverse(
                'ib_position_remove', kwargs={'obj_id': obj.id}
            ),
        )

    pos_manage.short_description = 'Position'
    pos_manage.allow_tags = True

    list_display = (
        'title', 'real_name', 'broker', 'account_id', 'path', 'capability',
        'ib_import', 'pos_manage'
    )
    fieldsets = (
        ('Primary', {'fields': (
            'title', 'real_name', 'broker', 'account_id', 'start', 'stop'
        )}),
        ('Detail', {'fields': (
            'path', 'account_type', 'customer_type', 'capability', 'description'
        )}),
    )

    search_fields = ('title', 'real_name', 'broker', 'account_id', 'description')
    list_filter = ('account_type', 'customer_type')
    list_per_page = 20


class StatementAdminInline(admin.TabularInline):
    extra = 0
    can_delete = False
    editable_fields = []
    readonly_fields = []
    exclude = ('statement',)

    def get_readonly_fields(self, request, obj=None):
        return list(self.readonly_fields) + \
               [field.name for field in self.model._meta.fields
                if field.name not in self.editable_fields and
                field.name not in self.exclude]

    def has_add_permission(self, request):
        return False


class IBNetAssetValueInline(StatementAdminInline):
    model = IBNetAssetValue


class IBMarkToMarketInline(StatementAdminInline):
    model = IBMarkToMarket
    # readonly_fields = fields_for_model(IBMarkToMarket).keys()


class IBPerformanceInline(StatementAdminInline):
    model = IBPerformance


class IBProfitLossInline(StatementAdminInline):
    model = IBProfitLoss


class IBCashReportInline(StatementAdminInline):
    model = IBCashReport


class IBOpenPositionInline(StatementAdminInline):
    model = IBOpenPosition


class IBPositionTradeInline(StatementAdminInline):
    model = IBPositionTrade


class IBFinancialInfoInline(StatementAdminInline):
    model = IBFinancialInfo


class IBInterestAccrualInline(StatementAdminInline):
    model = IBInterestAccrual


class IBStatementAdmin(admin.ModelAdmin):
    inlines = [
        IBNetAssetValueInline, IBMarkToMarketInline, IBPerformanceInline,
        IBProfitLossInline, IBCashReportInline, IBOpenPositionInline,
        IBPositionTradeInline, IBFinancialInfoInline, IBInterestAccrualInline
    ]

    def ib_import(self, obj):
        return '{link} | {xray}'.format(
            link='<a href="%s" target="_blank">Import</a>' % reverse(
                'ib_statement_import', kwargs={'obj_id': obj.statement_name.id}
            ),
            xray='<a href="%s" target="_blank">X-ray</a>' % reverse(
                'ib_statement_csv_symbol', kwargs={'obj_id': obj.id}
            )
        )

    ib_import.short_description = ''
    ib_import.allow_tags = True

    list_display = (
        'statement_name', 'date', 'stock_end', 'option_end', 'ib_import'
    )
    fieldsets = (
        ('Primary', {'fields': ('statement_name', 'date')}),
        ('Net Asset Value', {'fields': (
            'stock_prior', 'stock_trans', 'stock_pl_mtm_prior', 'stock_pl_mtm_trans', 'stock_end',
            'option_prior', 'option_trans', 'option_pl_mtm_prior', 'option_pl_mtm_trans', 'option_end',
        )}),

    )

    search_fields = ('statement_name__title', 'date')
    list_filter = ('statement_name__title',)
    list_per_page = 20


class IBPositionAdmin(admin.ModelAdmin):
    inlines = [
        IBMarkToMarketInline, IBPerformanceInline,
        IBProfitLossInline, IBOpenPositionInline,
        IBPositionTradeInline, IBFinancialInfoInline
    ]

    def report(self, obj):
        return '{report}'.format(
            report='<a href="%s" target="_blank">Report</a>' % reverse(
                'ib_position_report', kwargs={'obj_id': obj.id}
            ),
        )

    report.short_description = ''
    report.allow_tags = True

    list_display = (
        'symbol', 'date0', 'date1', 'status', 'statement_name', 'report'
    )
    fieldsets = (
        ('Primary', {'fields': (
            'statement_name', 'symbol', 'date0', 'date1', 'status',
        )}),
        ('Main (auto)', {'fields': (
            'fee', 'options', 'perform', 'total'
        )}),
        ('Main (select)', {'fields': (
            'updated', 'adjust', 'qty_multiply', 'move', 'side', 'account',
            'name', 'spread', 'strikes'
        )}),

    )

    search_fields = ('statement_name__title', 'symbol')
    list_filter = ('statement_name__title', 'status')
    list_per_page = 20

    readonly_fields = ('statement_name', )


admin.site.register(IBStatementName, IBStatementNameAdmin)
admin.site.register(IBStatement, IBStatementAdmin)
admin.site.register(IBPosition, IBPositionAdmin)
