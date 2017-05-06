from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from adminplus.sites import AdminSitePlus

admin.site = AdminSitePlus()
admin.autodiscover()
admin.site.site_header = 'Rivers'

urlpatterns = patterns(
    '',
    # app
    url(r'^base/', include('base.urls')),
    url(r'^opinion/', include('opinion.urls')),
    url(r'^broker/ib/', include('broker.ib.urls')),
    url(r'^subtool/', include('subtool.urls')),

    # admin
    url(r'^admin/', include(admin.site.urls)),

    # url(r'^algorithm/', include('research.algorithm.urls')),
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
