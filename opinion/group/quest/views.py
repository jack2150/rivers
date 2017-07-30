from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from opinion.group.quest.models import QuestLine


def report_questline(request, obj_id):
    """
    Goal tracking, show quest detail
    :param request: request
    :param obj_id: int
    :return: render
    """
    if int(obj_id):
        questline = QuestLine.objects.get(id=obj_id)
    else:
        try:
            questline = QuestLine.objects.filter(active=True).latest('stop')
        except ObjectDoesNotExist:
            questline = QuestLine.objects.latest('stop')

    title = 'Quest tracker - %s' % questline.name.upper()
    template = 'opinion/quest/index.html'
    parameters = {
        'title': title,
        'questline': questline
    }

    return render(request, template, parameters)




