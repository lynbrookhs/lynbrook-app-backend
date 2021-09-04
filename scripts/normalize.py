import csv

from core.models import Organization

with open("clubs.csv") as f:
    reader = csv.DictReader(f)
    clubs = list(reader)

with open("clubs_out.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=["Club Name", "Location", "Day", "Time"])
    writer.writeheader()
    for x in clubs:
        name = x["Club Name"]
        location = x["Location"]
        day = x["Day"]
        time = x["Time"]

        name = name.replace("Lynbrook", "").replace("Club", "").strip()

        try:
            obj = Organization.objects.get(name__icontains=name)
        except Organization.DoesNotExist:
            print(name)
        except Organization.MultipleObjectsReturned:
            try:
                obj = Organization.objects.get(name__icontains=name + " ")
            except Organization.DoesNotExist:
                print(name)
            except Organization.MultipleObjectsReturned:
                print("MULTIPLE", name)
        else:
            name = obj.name

        writer.writerow({"Club Name": name, "Location": location, "Day": day, "Time": time})
        # print(name, location, day, time, sep="\t\t")
