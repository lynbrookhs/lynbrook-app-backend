import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0055_delete_schedules"),
    ]

    operations = [
        migrations.AlterField(
            model_name="calendarevent",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="calendar_events",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="calendarevent",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="calendar_events",
                to="core.organization",
            ),
        ),
        migrations.AddField(
            model_name="calendarevent",
            name="location",
            field=models.CharField(blank=True, default="", max_length=200),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="calendarevent",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(user__isnull=False, organization__isnull=True)
                    | models.Q(user__isnull=True, organization__isnull=False)
                ),
                name="core_calendarevent_one_owner",
            ),
        ),
    ]
