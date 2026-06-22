from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0049_auto_20221017_2142'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='grad_year',
            field=models.IntegerField(blank=True, choices=[(2022, 2022), (2023, 2023), (2024, 2024), (2025, 2025), (2026, 2026), (2027, 2027), (2028, 2028), (2029, 2029), (2030, 2030)], null=True),
        ),
    ]
