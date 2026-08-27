from django.db import migrations


def move_links(apps, schema_editor):
    """Preserve Organization.link before dropping it.

    The field was never rendered anywhere in the app, but five clubs filled it
    in expecting it to show. OrganizationLink is the one that actually appears
    (in Settings), so each value moves there rather than being lost. Clubs that
    already list the same URL are skipped.
    """
    Organization = apps.get_model("core", "Organization")
    OrganizationLink = apps.get_model("core", "OrganizationLink")

    for org in Organization.objects.exclude(link__isnull=True).exclude(link=""):
        OrganizationLink.objects.get_or_create(
            organization=org, url=org.link, defaults={"title": "More Info"}
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0057_import_asb_calendar"),
    ]

    operations = [
        migrations.RunPython(move_links, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="organization",
            name="link",
        ),
    ]
