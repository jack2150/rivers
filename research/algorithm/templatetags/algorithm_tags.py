from django import template

register = template.Library()


@register.filter
def algo_para_name(obj):
    name = obj.replace('Handle_data_', '')
    name = name.replace('Create_signal_', '')
    name = name.replace('_', ' ').capitalize()

    return name
