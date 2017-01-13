from django.shortcuts import render
from opinion.group.mindset.models import MindsetBehavior
from opinion.group.mindset.models import MindsetNote


def trade_note(request, category):
    """
    Trade note reading view
    :param request: request
    :param category: str
    :return: render
    """
    trade_notes = MindsetNote.objects.filter(category=category)

    template = 'personal/mindset_note.html'

    title = '%s note review' % category.capitalize()
    parameters = dict(
        site_title=title,
        title=title,
        trade_notes=trade_notes
    )

    return render(request, template, parameters)


def behavior_profile(request, date):
    """
    Behaviour opinion profile
    :param request: request
    :param date: str
    :return: render
    """
    behavior_opinion = MindsetBehavior.objects.get(date=date)

    template = 'opinion/behavior_profile.html'

    parameters = dict(
        site_title='Behavior profile',
        title='Behavior profile: {date}'.format(
            date=date
        ),
        date=date,
        behavior_opinion=behavior_opinion
    )

    return render(request, template, parameters)
