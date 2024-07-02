from django.db import migrations


def add_location(apps, schema_editor):
    Team = apps.get_model("teams", "Team")
    Location = apps.get_model("tides", "Location")
    location, _ = Location.objects.get_or_create(
        name="Dana Point",
        defaults=dict(
            station_id="9410170",  # San Diego
            latitude=33.485,
            longitude=-117.735,
            time_zone="America/Los_Angeles",
        ),
    )
    team = Team.objects.create(name="Dana Point", slug="danapoint", location=location)


class Migration(migrations.Migration):

    dependencies = [
        ("teams", "0010_set_is_live"),
    ]

    operations = [
        migrations.RunPython(add_location, migrations.RunPython.noop),
    ]
