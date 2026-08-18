from django.db import migrations, models


def turn_toggles_off(apps, schema_editor):
    Membership = apps.get_model("core", "Membership")
    Membership.objects.update(calendar_events=False, receive_pings=False)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0051_calendar_events_and_pings"),
    ]

    operations = [
        migrations.AlterField(
            model_name="membership",
            name="calendar_events",
            field=models.BooleanField(
                default=False, help_text="Show this organization's meeting times in the user's calendar."
            ),
        ),
        migrations.AlterField(
            model_name="membership",
            name="receive_pings",
            field=models.BooleanField(
                default=False, help_text="Receive push notification pings from this organization's admins."
            ),
        ),
        migrations.RunPython(turn_toggles_off, migrations.RunPython.noop),
    ]
