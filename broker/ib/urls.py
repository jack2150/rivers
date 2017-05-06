from django.conf.urls import url, include

from broker.ib.views import *
from . import views

urlpatterns = [
    # object import
    url(r'^ibstatementname/import/(?P<ib_path>\w+)/$',
        ib_statement_imports, name='ib_statement_imports'),
    url(r'^ibstatement/import/(?P<obj_id>\d+)/$',
        ib_statement_import, name='ib_statement_import'),

    # position

    url(r'^ibstatementname/position/create/(?P<obj_id>\d+)/$',
        ib_position_create, name='ib_position_create'),
    url(r'^ibstatementname/position/remove/(?P<obj_id>\d+)/$',
        ib_position_remove, name='ib_position_remove'),
    url(r'^ibstatementname/position/report/(?P<obj_id>\d+)/$',
        ib_position_report, name='ib_position_report'),

    # report
    url(r'^ibstatementname/csv/create/(?P<obj_id>\d+)/$',
        views.ib_statement_create_csv, name='ib_statement_create_csv'),
    url(r'^ibstatement/truncate/(?P<obj_id>\d+)/$',
        views.ib_statement_truncate, name='ib_statement_truncate'),
    url(r'^ibstatement/csv/symbol/create/(?P<obj_id>\d+)/$',
        views.ib_statement_csv_symbol, name='ib_statement_csv_symbol'),

]
