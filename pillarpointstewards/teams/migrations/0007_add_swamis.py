from django.db import migrations


def add_swamis(apps, schema_editor):
    Team = apps.get_model("teams", "Team")
    Location = apps.get_model("tides", "Location")
    location, _ = Location.objects.get_or_create(
        name="Swami's Reef",
        defaults=dict(
            station_id="9410230",
            latitude=33.034741,
            longitude=-117.294032,
            time_zone="America/Los_Angeles",
        ),
    )
    team = Team.objects.create(name="Swami's Reef", slug="swamis", location=location)
    team.codes.create(code="SWAM", is_active=True)


class Migration(migrations.Migration):
    dependencies = [
        ("teams", "0006_assign_locations_to_teams"),
    ]

    operations = [
        migrations.RunPython(add_swamis, migrations.RunPython.noop),
    ]
