from django.conf.urls import url
from . import views

urlpatterns = [
    # main process & tools
    url(r'^tools/', views.tools, name='tools'),  # new
    url(r'^process/', views.process, name='process'),  # old

    # excel_date_price
    url(r'^date_price/$',
        views.excel_date_price, name='excel_date_price'),
]
