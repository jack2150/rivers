from django import template

register = template.Library()


@register.filter
def algo_para(obj):
    temp = {}
    exec 'temp = %s' % obj

    output = []
    for k, v in temp.items():
        output.append('%s=%s' % (k, v))

    return '<br>'.join(output)
