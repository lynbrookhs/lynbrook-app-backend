# Generated by Django 3.2.5 on 2021-09-14 08:26

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_auto_20210904_1531'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime.now),
            preserve_default=False,
        ),
    ]
