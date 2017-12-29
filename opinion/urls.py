from django.conf.urls import url, include

from opinion.group.mindset.views import *
from . import views

urlpatterns = [
    # position
    url(r'^position/', include('opinion.group.position.urls')),

    # report
    url(r'^report/enter/create/(?P<symbol>\w+)/$',
        views.report_enter_create, name='report_enter_create'),
    url(r'^report/enter/create/(?P<symbol>\w+)/(?P<date>\d{4}-\d{2}-\d{2})/$',
        views.report_enter_create, name='report_enter_create'),
    url(r'^report/enter/url/(?P<report_id>\d+)/(?P<model>\w+)/$',
        views.report_enter_link, name='report_enter_link'),
    url(r'^report/enter/summary/(?P<report_id>\d+)/$',
        views.report_enter_summary, name='report_enter_summary'),

    # market
    url(r'^market/week/create/(?P<obj_id>\d+)/$',
        views.market_week_create, name='market_week_create'),
    url(r'^market/month/economic/create/(?P<obj_id>\d+)/$',
        views.market_month_economic_create, name='market_month_economic_create'),
    url(r'^market/month/report/(?P<obj_id>\d+)/$',
        views.market_month_report, name='market_month_report'),
    url(r'^market/week/report/(?P<obj_id>\d+)/$',
        views.market_week_report, name='market_week_report'),
    url(r'^market/month/week/strategy/report/(?P<obj_id>\d+)/$',
        views.market_strategy_report, name='market_strategy_report'),

    # stock
    url(r'^stock/earning/report/(?P<symbol>\w+)/$',
        views.report_earning, name='report_earning'),

    # statement
    url(r'^statement/month/report/(?P<obj_id>\d+)/$',
        views.ib_month_statement_report, name='ib_month_statement_report'),

    # mindset
    url('mindsetnote/(?P<category>\w+)/$',
        trade_note, name='trade_note'),
    url('mindsetnote/(?P<date>\d{4}-\d{2}-\d{2})/$',
        behavior_profile, name='behavior_profile'),

    # questline
    url(r'^questline/report/(?P<obj_id>\d+)/$',
        views.report_questline, name='report_questline'),

    # option
    url(r'^optionstat/timesale/create/(?P<obj_id>\d+)/$',
        views.timesale_create, name='timesale_create'),
    url(r'optionstat/timesale/report/(?P<obj_id>\d+)/$',
        views.timesale_report, name='timesale_report'),
    url(r'optionstat/report/(?P<obj_id>\d+)/$',
        views.report_option_stat, name='report_option_stat'),

    # stat
    url(r'pricestat/report/basic/(?P<symbol>\w+)/$',
        views.report_statprice, name='report_statprice'),
    url(r'pricestat/report/stem/(?P<symbol>\w+)/(?P<percent>-?\d+)/(?P<bdays>\d+)/$',
        views.report_statstem, name='report_statstem'),

    # underlying
    url(r'^underlying/report/(?P<obj_id>\d+)/(?P<process>\w+)/$',
        views.underlying_report_create, name='underlying_report_create'),
]
