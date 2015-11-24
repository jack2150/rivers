from django.conf.urls import patterns, include, url
from django.contrib import admin
from adminplus.sites import AdminSitePlus

admin.site = AdminSitePlus()
admin.autodiscover()
admin.site.site_header = 'Rivers quantitative platform'

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
)
