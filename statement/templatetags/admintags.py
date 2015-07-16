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