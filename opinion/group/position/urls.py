from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^portfolio_latest', views.portfolio_latest, name='portfolio_latest'),

]
