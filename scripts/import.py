import csv

from core.models import ClubCategory, DayOfWeek, Organization, OrganizationType

with open("scripts/clubs_out_fixed.csv") as f:
    reader = csv.DictReader(f)
    clubs = list(reader)

for x in clubs:
    name = x["Club Name"]
    location = x["Location"]
    day = x["Day"]
    time = x["Time"]

    if location.isdigit():
        location = f"Room {int(location):03}"

    obj, _ = Organization.objects.get_or_create(
        name=name, defaults=dict(type=OrganizationType.CLUB, category=ClubCategory.INTEREST)
    )
    if day:
        obj.day = getattr(DayOfWeek, day.upper())
    obj.location = location
    obj.time = time
    obj.save()

    print(obj)
