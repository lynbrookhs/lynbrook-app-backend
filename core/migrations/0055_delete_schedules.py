from django.db import migrations


class Migration(migrations.Migration):
    """Drop the bell-schedule models.

    Nothing consumed them: no app screen or website template referenced a
    schedule, and /api/schedules/ took zero requests over the preceding week.
    The data was dumped to lynbrook-backups/20260826-schedules-before-drop.sql
    before this ran.
    """

    dependencies = [
        ("core", "0054_remove_event_link"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="scheduleperiod",
            name="period",
        ),
        migrations.RemoveField(
            model_name="scheduleperiod",
            name="schedule",
        ),
        migrations.DeleteModel(name="SchedulePeriod"),
        migrations.DeleteModel(name="Schedule"),
        migrations.DeleteModel(name="Period"),
    ]
