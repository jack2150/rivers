from django.shortcuts import render
from opinion.personal.models import BehaviorOpinion


def behavior_profile(request, date):
    """
    Behaviour opinion profile
    :param request: request
    :param date: str
    :return: render
    """
    behavior_opinion = BehaviorOpinion.objects.get(date=date)

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
