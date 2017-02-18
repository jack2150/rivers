from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^position/', include('opinion.group.position.urls')),

    url(r'^enter/report/create/(?P<symbol>\w+)/$',
        views.generate_report, name='report_create'),
    url(r'^enter/report/create/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
        views.generate_report, name='report_create'),
    url(r'^enter/report/url/(?P<report_id>\d+)/(?P<model>\w+)/$',
        views.reference_link, name='report_url'),
    url(r'^enter/report/summary/(?P<report_id>\d+)/$',
        views.enter_report, name='enter_report'),
]
