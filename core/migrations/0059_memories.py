import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0058_remove_organization_link"),
    ]

    operations = [
        migrations.CreateModel(
            name="MemoryRelease",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("grad_year", models.IntegerField(unique=True)),
                ("released_at", models.DateTimeField(auto_now_add=True)),
                ("released_by", models.CharField(blank=True, max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name="Memory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "grad_year",
                    models.IntegerField(help_text="Senior class this memory belongs to (controls its release)."),
                ),
                ("photo", models.ImageField(upload_to="memories/")),
                ("note", models.CharField(blank=True, max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "recipients",
                    models.ManyToManyField(blank=True, related_name="received_memories", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "sender",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sent_memories",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
                "verbose_name_plural": "Memories",
            },
        ),
    ]
