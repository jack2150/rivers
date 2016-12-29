from django.shortcuts import render
from opinion.plan.models import TradeNote


def trade_note(request, category):
    """
    Trade note reading view
    :param request: request
    :param category: str
    :return: render
    """
    trade_notes = TradeNote.objects.filter(category=category)

    template = 'plan/trade_note.html'

    title = '%s note review' % category.capitalize()
    parameters = dict(
        site_title=title,
        title=title,
        trade_notes=trade_notes
    )

    return render(request, template, parameters)
