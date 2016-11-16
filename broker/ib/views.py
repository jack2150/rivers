import glob
import os
from django.shortcuts import render, redirect
from broker.ib.models import *
from rivers.settings import IB_STATEMENT_DIR


def ib_statement_import(request, broker_id, date):
    """
    Import IB statement single date
    :param broker_id: str
    :param date: str
    :param request: request
    :return: redirect
    """
    ib_statement = IBStatement.objects.get(name__broker_id=broker_id, date=date)
    date_str = ib_statement.date.strftime('%Y%m%d')
    fname = '%s_%s_%s.csv' % (broker_id.upper(), date_str, date_str)
    ib_statement.statement_import(ib_statement.name, fname)

    return redirect('admin:ib_ibstatement_changelist')


def ib_statement_imports(request, ib_path):
    """
    Import IB  statement import all in folder
    :param ib_path: str
    :param request: request
    :return: redirect
    """
    ib_statement_name = IBStatementName.objects.get(path=ib_path)

    folder_path = os.path.join(IB_STATEMENT_DIR, ib_statement_name.path, '*.csv')
    paths = glob.glob(folder_path)
    for path in paths:
        fname = os.path.basename(path)
        date = datetime.strptime(fname.split('_')[-1].split('.')[0], '%Y%m%d')

        ib_statement = IBStatement()
        ib_statement.name = ib_statement_name
        ib_statement.date = date
        ib_statement.save()

        ib_statement.statement_import(ib_statement.name, fname)

    return redirect('admin:ib_ibstatement_changelist')
