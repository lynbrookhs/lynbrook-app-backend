from datetime import datetime, timezone

from django.db import migrations

# The Lynbrook ASB 2026-27 events, lifted out of static/asb-events-2026-27.ics so
# they can be edited in the admin instead of by hand-editing a file on the server.
# Times were converted from America/Los_Angeles to UTC at import.
EVENTS = [
    ('Freshmen Club Showcase', 'Quad', "2026-08-11T19:00:00Z", "2026-08-11T20:00:00Z", False),
    ('Senior Sunrise', 'Stober Field', "2026-08-21T13:00:00Z", "2026-08-21T15:30:00Z", False),
    ('Mandatory Class Meeting', 'Gym/Cafe/Field House/Auditorium', "2026-08-21T17:10:00Z", "2026-08-21T17:50:00Z", False),
    ('Welcome Back Rally', 'Gym', "2026-08-28T17:10:00Z", "2026-08-28T17:50:00Z", False),
    ('Welcome Back Event', 'Quad/Cafe', "2026-08-28T23:00:00Z", "2026-08-29T03:00:00Z", False),
    ('New Club Application Info Meeting', 'ASB Classroom', "2026-09-18T19:45:00Z", "2026-09-18T20:25:00Z", False),
    ('Optional Class Meeting', 'Gym/Cafe/Field House/Auditorium', "2026-09-30T17:10:00Z", "2026-09-30T17:50:00Z", False),
    ('SVT Game #1', 'Gym', "2026-10-02T19:45:00Z", "2026-10-02T20:25:00Z", False),
    ('Football Pep Rally', 'Quad', "2026-10-16T19:45:00Z", "2026-10-16T20:25:00Z", False),
    ('Homecoming Court', 'Stadium', "2026-10-17T02:00:00Z", "2026-10-17T04:00:00Z", False),
    ('Homecoming Dance', 'Quad/Cafe', "2026-10-18T02:00:00Z", "2026-10-18T04:30:00Z", False),
    ('HOCO Rec Party', 'Cafeteria', "2026-10-28T22:00:00Z", "2026-10-29T00:00:00Z", False),
    ('Trick or Treating', 'Campus', "2026-10-30T17:50:00Z", "2026-10-30T18:05:00Z", False),
    ('Fall Rally', 'Gym', "2026-11-13T18:10:00Z", "2026-11-13T18:50:00Z", False),
    ('Flea Market', 'Quad', "2026-11-20T20:45:00Z", "2026-11-21T01:00:00Z", False),
    ('Student Wellness Panel', 'Online', "2027-01-22T03:00:00Z", "2027-01-22T04:00:00Z", False),
    ('Blacklit Rally', 'Gym', "2027-01-29T18:10:00Z", "2027-01-29T18:50:00Z", False),
    ('Club Food Day', 'Quad + Hallways', "2027-02-05T20:45:00Z", "2027-02-05T21:25:00Z", False),
    ('Senior Class Meeting', 'Theater', "2027-02-10T18:10:00Z", "2027-02-10T18:50:00Z", False),
    ('Valentines Day Activity', 'Quad', "2027-02-12T20:45:00Z", "2027-02-12T21:25:00Z", False),
    ('Coffee House Talentshow', 'Cafeteria', "2027-02-13T03:00:00Z", "2027-02-13T05:30:00Z", False),
    ('Munch Madness', 'Quad', "2027-03-05T20:45:00Z", "2027-03-05T21:25:00Z", False),
    ('Holi', 'Staff Parking Lot', "2027-03-12T23:15:00Z", "2027-03-13T01:00:00Z", False),
    ('St. Patricks Day Scavenger Hunt', 'Quad', "2027-03-17T19:45:00Z", "2027-03-17T20:25:00Z", False),
    ('Spring Event', 'Quad/Cafe', "2027-03-19T23:00:00Z", "2027-03-20T05:00:00Z", False),
    ('Culture Festival', 'Quad/Cafeteria', "2027-04-09T23:00:00Z", "2027-04-10T02:00:00Z", False),
    ('SVT Game #2', 'Gym', "2027-04-23T19:45:00Z", "2027-04-23T20:25:00Z", False),
    ('Film Fest', 'Auditorium', "2027-05-15T02:00:00Z", "2027-05-15T04:00:00Z", False),
    ('Farewell Rally', 'Gym', "2027-05-21T17:10:00Z", "2027-05-21T17:50:00Z", False),
    ('Indesign Fashion Show', 'Quad/Cafe/Staff', "2027-05-21T23:00:00Z", "2027-05-22T05:00:00Z", False),
    ('Senior Sunset/Picnic', 'Basketball Courts/Football Field', "2027-05-29T00:00:00Z", "2027-05-29T04:00:00Z", False),
    ('Week of Welcome', 'Quad', "2026-08-17T15:30:00Z", "2026-08-21T20:25:00Z", False),
    ('Spirit Week', 'Quad', "2026-08-24T15:30:00Z", "2026-08-27T21:10:00Z", False),
    ('Vikepound Sales', 'Den', "2026-08-26T15:30:00Z", "2026-08-28T20:25:00Z", False),
    ('Club Info Week', 'Quad', "2026-09-02T15:30:00Z", "2026-09-04T20:25:00Z", False),
    ('Game Show/Trivia Week', 'Quad', "2026-09-08T15:30:00Z", "2026-09-11T20:25:00Z", False),
    ('Breast Cancer Awareness Week', 'Quad', "2026-09-28T15:30:00Z", "2026-10-02T20:25:00Z", False),
    ('HOCO', 'Quad', "2026-10-13T15:30:00Z", "2026-10-16T17:50:00Z", False),
    ('Haunted House', '', "2026-10-29T07:00:00Z", "2026-10-31T07:00:00Z", True),
    ('THANKSGIVING', '', "2026-11-25T08:00:00Z", "2026-11-28T08:00:00Z", True),
    ('Winter Wellness Week', 'Quad', "2026-12-07T16:30:00Z", "2026-12-11T21:25:00Z", False),
    ('WINTER BREAK', '', "2026-12-21T08:00:00Z", "2027-01-02T08:00:00Z", True),
    ('Lynbrook Idol Auditions', 'Den', "2027-01-11T16:30:00Z", "2027-01-15T21:25:00Z", False),
    ('Lynbrook Idol Performances', 'Quad', "2027-01-20T16:30:00Z", "2027-01-22T21:25:00Z", False),
    ('Spirit Week', 'Campus', "2027-01-25T16:30:00Z", "2027-01-29T21:25:00Z", False),
    ('Lunar New Year', 'Den', "2027-02-03T16:30:00Z", "2027-02-05T21:25:00Z", False),
    ('SKI BREAK', '', "2027-02-15T08:00:00Z", "2027-02-20T08:00:00Z", True),
    ('Senior Games', 'Football Field/Quad/Gym', "2027-03-08T16:30:00Z", "2027-03-26T20:25:00Z", False),
    ('Spring Wellness Week', '', "2027-03-22T07:00:00Z", "2027-03-27T07:00:00Z", True),
    ('SPRING BREAK', '', "2027-04-12T07:00:00Z", "2027-04-17T07:00:00Z", True),
    ('Charity Week', 'Quad', "2027-04-19T15:30:00Z", "2027-04-23T20:25:00Z", False),
    ('Spring Egg Hunt', 'Around Campus', "2027-04-26T07:00:00Z", "2027-05-01T07:00:00Z", True),
    ('May "Mental Health" Week', 'Quad', "2027-05-10T15:30:00Z", "2027-05-14T20:25:00Z", False),
    ('Senior Farewell Week', 'Campus', "2027-05-17T15:30:00Z", "2027-05-20T21:10:00Z", False),
]


ASB_ORG_ID = 2


def load(apps, schema_editor):
    Organization = apps.get_model("core", "Organization")
    CalendarEvent = apps.get_model("core", "CalendarEvent")

    try:
        org = Organization.objects.get(id=ASB_ORG_ID)
    except Organization.DoesNotExist:
        return

    def parse(value):
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    for title, location, start, end, all_day in EVENTS:
        CalendarEvent.objects.get_or_create(
            organization=org,
            title=title,
            start=parse(start),
            defaults={"location": location, "end": parse(end), "all_day": all_day},
        )


def unload(apps, schema_editor):
    CalendarEvent = apps.get_model("core", "CalendarEvent")
    CalendarEvent.objects.filter(
        organization_id=ASB_ORG_ID, title__in=[title for title, *_ in EVENTS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0056_calendarevent_organization"),
    ]

    operations = [migrations.RunPython(load, unload)]
