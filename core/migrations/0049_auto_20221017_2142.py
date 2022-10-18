# Generated by Django 3.2.5 on 2022-10-18 04:42

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0048_alter_user_grad_year'),
    ]

    operations = [
        migrations.CreateModel(
            name='WordleTheme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('word', models.CharField(max_length=5)),
            ],
        ),
        migrations.AlterField(
            model_name='wordleentry',
            name='word',
            field=models.CharField(default=core.models.wordle_key, max_length=5),
        ),
    ]