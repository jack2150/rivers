# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ib', '0002_auto_20161113_2002'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ibnetassetvalue',
            name='date',
        ),
    ]
