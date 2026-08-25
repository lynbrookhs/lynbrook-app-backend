from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0052_toggles_default_off"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="link",
            field=models.URLField(
                blank=True,
                default="",
                help_text=(
                    "Link events only. The home screen shows these like the Daily Wordle: tapping the "
                    "arrow awards the points once, then opens this URL."
                ),
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="submission_type",
            field=models.IntegerField(choices=[(1, "Code"), (2, "File"), (3, "Link")], default=1),
        ),
    ]
