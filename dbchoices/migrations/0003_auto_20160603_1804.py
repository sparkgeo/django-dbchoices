# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dbchoices', '0002_choice_category'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='choice',
            unique_together=set([('content_type', 'category', 'field_name', 'value', 'display')]),
        ),
    ]
