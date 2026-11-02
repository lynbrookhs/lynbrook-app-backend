from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0060_pointsadjustment"),
    ]

    operations = [
        migrations.AddField(
            model_name="memory",
            name="reviewed",
            field=models.BooleanField(default=False, help_text="Checked off by a moderator."),
        ),
        migrations.AddField(
            model_name="user",
            name="memories_opt_out",
            field=models.BooleanField(
                default=False, help_text="Senior has opted out of being tagged in new memories."
            ),
        ),
    ]
