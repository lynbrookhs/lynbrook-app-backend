from django.db import migrations, models
from django.utils import timezone


def retire_link_events(apps, schema_editor):
    """Turn any remaining link events into ended file events.

    Link events used submission_type 3, which this migration removes. Their
    submissions (and so the points already awarded for them) are left alone —
    only the event's own type and end date change.
    """
    Event = apps.get_model("core", "Event")
    now = timezone.now()
    for event in Event.objects.filter(submission_type=3):
        event.submission_type = 2
        event.link = ""
        if event.end > now:
            event.end = now
        event.save()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0053_event_link"),
    ]

    operations = [
        migrations.RunPython(retire_link_events, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="event",
            name="link",
        ),
        migrations.AlterField(
            model_name="event",
            name="submission_type",
            field=models.IntegerField(choices=[(1, "Code"), (2, "File")], default=1),
        ),
    ]
