import json
import lxml.html
from datetime import datetime
import re
from django import template

register = template.Library()


@register.filter
def tabular_style(obj):
    obj = str(obj)
    if 'vTextField' in obj:
        line = obj.replace('vTextField', '')
        line = line[:-2] + ' style="width: 70px;" ' + line[-2:]
    else:
        line = obj
        line = line[:-2] + ' style="width: 55px;" ' + line[-2:]
    return line


@register.filter
def tabular_textarea(obj):
    obj = str(obj)
    if 'vLargeTextField' in obj:
        line = obj.replace('vLargeTextField', '')
        line = line.replace('rows="10"', 'rows="4"')
    else:
        line = obj
    return line


@register.filter
def admin_field_type(obj):
    return obj.field.field.widget.__class__.__name__


@register.filter
def fieldset_id(name):
    return re.sub('[^a-zA-Z]+', '', name)


@register.filter
def label(name):
    return ' '.join(name.split('_')).capitalize()


@register.filter
def admin_log_json(logs):
    data = []
    for entry in logs:
        line = {}
        if entry.is_deletion() or not entry.get_admin_url():
            line['link'] = ""
            line['title'] = str(entry.object_repr)
        else:
            line['link'] = entry.get_admin_url()
            line['title'] = str(entry.object_repr)

        if entry.content_type:
            line['text'] = str(entry.content_type)
        else:
            line['text'] = "Unknown content"

        data.append(line)

    return json.dumps(data)


@register.filter
def custom_view_json(custom_list):
    data = []
    for path, name in custom_list:
        data.append({
            'path': path,
            'name': name
        })

    return json.dumps(data)


@register.filter
def changelist_item(item):
    html = lxml.html.fromstring(item)

    for tag in html.xpath('//*[@class]'):
        # For each element with a class attribute, remove that class attribute
        tag.attrib.pop('class')

    result = str(lxml.html.tostring(html))
    result = result.replace('<th>', '<td>').replace('</th>', '</td>')

    return result


@register.filter
def filter_choice_json(choices):
    data = []
    for choice in choices:
        data.append({
            "selected": choice["selected"],
            "link": choice["query_string"],
            "display": str(choice["display"])
        })

    return json.dumps(data)


def date_handler(obj):
    """
    json date handler
    :param obj:
    :return:
    """
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError


@register.filter
def fieldset_json(fieldset):
    # print help(fieldset)
    data = []
    fields = []
    for line in fieldset:
        temp = {
            'error': True if line.errors() else False,
            'length': len(line.fields),
            'visible': True if line.has_visible_field else False,
            'error_line': line.errors(),
        }

        for field in line:
            try:
                getattr(field, 'is_readonly')
                is_readonly = field.is_readonly
                contents = field.contents
            except AttributeError:
                is_readonly = False
                contents = ''

            # field
            # print field.field



            #help(field.field.field)

            #print field.field.as_widget().__class__.__name__
            widget = field.field.field.widget.__class__.__name__
            field3x = field.field.field
            value = field.field.value()
            value = value if value else ''
            name = field.field.name
            auto_id = field.field.auto_id
            label = field.field.label
            # help_text = field.field.help_text
            print widget, name, auto_id, value, label
            if widget == 'Select':
                # help(field3x)
                # help(field.field)
                choices = [{'id': k, 'value': v} for k, v in field3x.widget.choices]
                too_long = any([True if len(c['value']) > 20 else False for c in choices])
                print choices,
                print auto_id, value
                # id_xxx
                if too_long:
                    control = {
                        "view": "combo", "label": label, "options": choices,
                        "labelWidth": 180, "width": 600, "value": value
                    }
                elif len(choices) > 4:
                    control = {
                        "view": "combo", "label": label, "options": choices,
                        "labelWidth": 180, "width": 400, "value": value
                    }
                else:
                    control = {
                        "view": "radio",
                        "name": auto_id,
                        "label": label,
                        "options": choices,
                        "value": value,
                        "labelWidth": 180,
                        # "inputHeight": 30
                        # "optionHeight": 100,
                        # "help_text": help_text
                    }




                fields.append(control)

                """
                fields.append({
                    'name': field.field.name,
                    'is_readonly': is_readonly,
                    'errors': field.errors(),
                    'hidden': field.field.is_hidden,
                    'is_checkbox': field.is_checkbox,
                    # 'label_tag': field.label_tag(),
                    'contents': contents,
                    'help_text': field.field.help_text,
                    'field': control
                })
                """
            elif widget in ('AdminDateWidget', 'DateTimePicker'):
                today = datetime.today().date()
                control = {
                    "view": "datepicker", "label": label, "name": name,
                    "stringResult": True, "labelWidth": 180, "width": 400,
                    "value": value if value else today
                }
                fields.append(control)
            elif widget == 'AdminIntegerFieldWidget':
                control = {
                    "view": "counter", "label": label, "width": 400, "name": auto_id,
                    "labelWidth": 180, "value": value
                }
                fields.append(control)
            elif widget == 'CheckboxInput':
                control = {
                    "view": "checkbox", "label": label, "name": auto_id,
                    "labelWidth": 180, "value": value
                }
                fields.append(control)
            elif widget in ('AdminTextInputWidget', 'NumberInput'):
                control = {
                    "view": "text", "value": value, "label": label, "name": auto_id,
                    "width": 400, "labelWidth": 180,
                }
                fields.append(control)
            elif widget == 'AdminTextareaWidget':
                control = {
                    "view": "textarea", "label": label, "labelPosition": "left",
                    "height": 120, "width": 600, "labelWidth": 180,
                }
                fields.append(control)
            else:
                raise LookupError('Unknown widget: %s' % widget)

        temp['fields'] = fields

        # data.append(fields)
    data = fields

    return json.dumps(data, default=date_handler)


@register.filter()
def minus(obj0, obj1):
    """
    json date handler
    :param obj1: int/float
    :param obj0: int/float
    :return: int/float
    """
    return obj0 - obj1


@register.filter()
def mean(obj0, obj1):
    """
    Mean of 2 values
    :param obj1: int/float
    :param obj0: int/float
    :return: int/float
    """
    return round((obj0 + obj1) / 2.0, 2)


@register.filter()
def multiply(obj0, obj1):
    """
    Mean of 2 values
    :param obj1: int/float
    :param obj0: int/float
    :return: int/float
    """
    return obj0 * obj1
