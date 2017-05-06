from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^tools/', views.tools, name='tools'),

    url(r'^process/', views.process, name='process'),
    url(r'^market/', views.market, name='market_reference'),

    # quote reference
    url(r'^reference/$', views.reference, name='quote_reference'),
    url(r'^reference/(?P<symbol>\w+)/$', views.reference, name='quote_reference'),

    # main progress
    url(r'^progress/', views.progress, name='progress'),


    # excel_date_price
    url(r'^date_price/$',
        views.excel_date_price, name='excel_date_price'),
]
