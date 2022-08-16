# Generated by Django 3.2.5 on 2022-08-16 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0047_user_wordle_streak'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='grad_year',
            field=models.IntegerField(blank=True, choices=[(2022, 2022), (2023, 2023), (2024, 2024), (2025, 2025), (2026, 2026)], null=True),
        ),
    ]
