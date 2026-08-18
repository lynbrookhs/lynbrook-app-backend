import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0050_alter_user_grad_year_2030"),
    ]

    operations = [
        migrations.AddField(
            model_name="membership",
            name="calendar_events",
            field=models.BooleanField(
                default=True, help_text="Show this organization's meeting times in the user's calendar."
            ),
        ),
        migrations.AddField(
            model_name="membership",
            name="receive_pings",
            field=models.BooleanField(
                default=True, help_text="Receive push notification pings from this organization's admins."
            ),
        ),
        migrations.CreateModel(
            name="Ping",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "message",
                    models.CharField(
                        help_text="Short message sent as a push notification to members' phones.", max_length=150
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="pings", to="core.organization"
                    ),
                ),
                (
                    "sent_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="CalendarEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("start", models.DateTimeField()),
                ("end", models.DateTimeField()),
                ("all_day", models.BooleanField(default=False)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="calendar_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("start",),
            },
        ),
    ]
