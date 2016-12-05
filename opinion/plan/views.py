from django.shortcuts import render
from opinion.plan.models import TradeNote


def trade_note(request):
    """
    Trade note reading view
    :param request: request
    :return: render
    """
    trade_notes = TradeNote.objects.order_by('date').reverse().all()

    template = 'plan/trade_note.html'

    parameters = dict(
        site_title='Trade note review',
        title='Trade note review',
        trade_notes=trade_notes
    )

    return render(request, template, parameters)
