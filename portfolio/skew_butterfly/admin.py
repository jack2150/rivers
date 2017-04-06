from django.contrib import admin
from portfolio.skew_butterfly.models import SkewButterfly, SkewButterflySet


class SkewButterflyInline(admin.TabularInline):
    model = SkewButterfly
    extra = 0


class SkewButterflySetAdmin(admin.ModelAdmin):
    inlines = [SkewButterflyInline]

    list_display = (
        'name', 'create_date', 'expire_date', 'capital', 'risk'
    )
    fieldsets = (
        ('Primary key', {
            'fields': (
                'name', 'create_date', 'expire_date', 'capital', 'risk'
            )
        }),
    )

    search_fields = ()
    list_per_page = 20


admin.site.register(SkewButterflySet, SkewButterflySetAdmin)
