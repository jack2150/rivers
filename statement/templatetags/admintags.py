from django import template

register = template.Library()


@register.filter
def admin_field_type(obj):
    return obj.field.field.widget.__class__.__name__