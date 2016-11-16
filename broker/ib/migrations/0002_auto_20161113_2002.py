# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ib', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ibstatementname',
            old_name='start_date',
            new_name='start',
        ),
        migrations.RenameField(
            model_name='ibstatementname',
            old_name='stop_date',
            new_name='stop',
        ),
    ]
