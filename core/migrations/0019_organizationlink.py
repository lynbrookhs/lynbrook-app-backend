# Generated by Django 3.2.5 on 2021-08-08 10:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20210808_0301'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('url', models.URLField()),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', to='core.organization')),
            ],
        ),
    ]
