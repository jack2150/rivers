from django import forms
from django.contrib import admin
from django.forms import RadioSelect

from opinion.group.report.admin import OpinionAdmin, OpinionStackedAdmin
from opinion.group.technical.models import *


class TechnicalRankForm(forms.ModelForm):
    class Meta:
        model = TechnicalRank
        widgets = {
            'market_edge': RadioSelect,
        }
        fields = '__all__'


class TechnicalMarketedgeAdmin(OpinionStackedAdmin):
    model = TechnicalMarketedge


class TechnicalBarchartAdmin(OpinionStackedAdmin):
    model = TechnicalBarchart


class TechnicalChartmillAdmin(OpinionStackedAdmin):
    model = TechnicalChartmill


class TechnicalRankAdmin(OpinionAdmin):
    inlines = [TechnicalMarketedgeAdmin, TechnicalBarchartAdmin, TechnicalChartmillAdmin]

    list_display = (
        'report',
        'technicalmarketedge', 'technicalbarchart', 'technicalchartmill',
    )
    fieldsets = (
        ('Foreign key', {
            'fields': ('report', )
        }),
    )

    search_fields = ('report__symbol', 'report__date',)
    list_per_page = 20

    readonly_fields = ('report', )


class TechnicalTickAdmin(OpinionStackedAdmin):
    model = TechnicalTick


class TechnicalSMAAdmin(OpinionStackedAdmin):
    model = TechnicalSma


class TechnicalVolumeAdmin(OpinionStackedAdmin):
    model = TechnicalVolume


class TechnicalIchimokuAdmin(OpinionStackedAdmin):
    model = TechnicalIchimoku


class TechnicalParabolicAdmin(OpinionStackedAdmin):
    model = TechnicalParabolic


class TechnicalStochAdmin(OpinionStackedAdmin):
    model = TechnicalStoch


class TechnicalBandAdmin(OpinionStackedAdmin):
    model = TechnicalBand


class TechnicalFwAdmin(OpinionStackedAdmin):
    model = TechnicalFw


class TechnicalTTMAdmin(OpinionStackedAdmin):
    model = TechnicalTTM


class TechnicalPivotAdmin(OpinionStackedAdmin):
    model = TechnicalPivot


class TechnicalFreeMoveAdmin(OpinionStackedAdmin):
    model = TechnicalFreeMove


class TechnicalZigZagAdmin(OpinionStackedAdmin):
    model = TechnicalZigZag


class TechnicalOpinionAdmin(OpinionAdmin):
    inlines = [
        TechnicalTickAdmin, TechnicalSMAAdmin, TechnicalVolumeAdmin, TechnicalIchimokuAdmin,
        TechnicalParabolicAdmin, TechnicalStochAdmin, TechnicalBandAdmin, TechnicalFwAdmin,
        TechnicalTTMAdmin, TechnicalPivotAdmin, TechnicalFreeMoveAdmin, TechnicalZigZagAdmin
    ]

    list_display = (
        'report',
    )
    fieldsets = (
        ('Primary', {
            'fields': ('report', )
        }),
    )

    search_fields = ('report__symbol', 'report__date',)
    readonly_fields = ('report',)
    list_per_page = 20


admin.site.register(TechnicalRank, TechnicalRankAdmin)
admin.site.register(TechnicalOpinion, TechnicalOpinionAdmin)
