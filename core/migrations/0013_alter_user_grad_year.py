# Generated by Django 3.2.5 on 2021-08-06 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_user_picture_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='grad_year',
            field=models.IntegerField(null=True),
        ),
    ]
