# Generated by Django 3.2.5 on 2021-08-09 23:59

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_auto_20210809_0921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='code',
            field=models.PositiveIntegerField(default=core.models.random_code),
        ),
    ]