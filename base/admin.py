from bootstrap3_datetime.widgets import DateTimePicker
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User, Group


class DateForm(forms.ModelForm):
    date = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


class StartStopForm(forms.ModelForm):
    start = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )

    stop = forms.DateField(
        widget=DateTimePicker(options={"format": "YYYY-MM-DD", "pickTime": False})
    )


admin.site.unregister(User)
admin.site.unregister(Group)
