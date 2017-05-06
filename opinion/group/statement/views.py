from django.shortcuts import render
from opinion.group.statement.models import IBMonthStatement


def ib_month_statement_report(request, obj_id):
    """
    IBMonthStatement report
    :param request: request
    :param obj_id: int
    :return: render
    """
    ib_month_statement = IBMonthStatement.objects.get(id=obj_id)

    template = 'opinion/statement/report.html'

    parameters = dict(
        site_title='IB Month Statement report',
        title='IB Month Statement report',
        ib_month_statement=ib_month_statement,
    )

    return render(request, template, parameters)
