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
    url(r'^stock/ownership/date_price/(?P<symbol>\w+)/$',
        views.ownership_price, name='ownership_price'),

    url(r'^stock/earning/report/(?P<symbol>\w+)/$',
        views.report_earning, name='report_earning'),

    # statement
    url(r'^statement/month/report/(?P<obj_id>\d+)/$',
        views.ib_month_statement_report, name='ib_month_statement_report'),

    # mindset
    url('mindsetnote/(?P<category>\w+)/$',
        trade_note, name='trade_note'),
    url('mindsetnote/(?P<date>\d{4}-\d{2}-\d{2})/$',
        behavior_profile, name='behavior_profile')
]
