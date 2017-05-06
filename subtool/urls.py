from django.conf.urls import url, include

from subtool.live.excel_rtd.views import excel_rtd_create
from subtool.option.timesale.views import timesale_insert_view, timesale_report_view
from subtool.ticker.minute1.views import minute1_si_report

urlpatterns = [
    # position
    url(
        'optiontimesale/insert',
        name='timesale_insert_view', view=timesale_insert_view
    ),
    url(
        'optiontimesale/report/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
        name='timesale_report_view', view=timesale_report_view
    ),
    url(
        'live/excel_rtd/create',
        name='excel_rtd_create', view=excel_rtd_create
    ),
    url(
        'subtool/ticker/minute1/si/report/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
        name='minute1_si_report', view=minute1_si_report
    )

]
