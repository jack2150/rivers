from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^process/', views.process, name='process'),
    url(r'^market/', views.market, name='market_reference'),

    # quote reference
    url(r'^reference/$', views.reference, name='quote_reference'),
    url(r'^reference/(?P<symbol>\w+)/$', views.reference, name='quote_reference'),


    url(r'^progress/', views.progress, name='progress'),
]
