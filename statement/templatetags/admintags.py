from django import template

register = template.Library()


@register.filter
def admin_field_type(obj):
    return obj.field.field.widget.__class__.__name__


@register.filter
def form_field_type(obj):
    return obj.field.widget.__class__.__name__


@register.filter
def field_name(obj):
    return ' '.join(obj.split('_'))


@register.filter
def field_name_last(obj):
    return obj.split('_')[-1].capitalize()


@register.filter
def intcomma(obj):
    return '{:,}'.format(obj)


@register.filter
def get_item(obj, name):
    return obj[name]


@register.filter
def convert_abs(obj):
    if type(obj) in (float, int):
        return abs(obj)
    else:
        return ''


@register.filter
def cap(obj):
    if obj:
        return obj.replace('_', ' ').capitalize()
    else:
        return ''


@register.filter
def algorithm_args(obj):
    """
    Algorithm arguments into a list
    :param obj: str
    :return: str
    """
    arguments = eval(obj)

    handle_data = arguments['handle_data']
    create_signal = arguments['create_signal']

    return handle_data.values() + create_signal.values()


@register.filter
def strategy_args(obj):
    """
    Strategy arguments into a list
    :param obj: str
    :return: str
    """
    try:
        args = sorted(eval(obj).values(), reverse=True)
    except AttributeError:
        args = []

    return args


@register.filter
def first_item(obj, key):
    return obj[0][key]


@register.filter
def percent(obj):
    try:
        result = '{percent}%'.format(percent=round(obj * 100.0, 2))
    except TypeError:
        result = obj
    return result


@register.filter
def percent2(obj):
    try:
        result = '{0:+.2f}%'.format(round(obj * 100.0, 2))
    except TypeError:
        result = obj
    return result


@register.filter
def index(item, i):
    return item[int(i - 1)]
