from django.conf.urls import patterns, include, url
from django.contrib import admin
from adminplus.sites import AdminSitePlus

admin.site = AdminSitePlus()
admin.autodiscover()
admin.site.site_header = 'Rivers'

urlpatterns = patterns(
    '',
    # app
    url(r'^base/', include('base.urls')),
    url(r'^opinion/', include('opinion.urls')),

    # admin
    url(r'^admin/', include(admin.site.urls)),
    # url(r'^algorithm/', include('research.algorithm.urls')),
)
