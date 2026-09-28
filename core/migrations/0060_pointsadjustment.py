from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0059_memories'),
    ]

    operations = [
        migrations.CreateModel(
            name='PointsAdjustment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delta', models.IntegerField(help_text='Change to the total (new total minus old total).')),
                ('year_delta', models.IntegerField(help_text='Portion charged to the school year this was made in. Equals delta for additions; a reduction is charged to the current year only up to its balance, the rest comes off prior years.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('membership', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='adjustments', to='core.membership')),
            ],
            options={
                'ordering': ('-created_at',),
            },
        ),
    ]
