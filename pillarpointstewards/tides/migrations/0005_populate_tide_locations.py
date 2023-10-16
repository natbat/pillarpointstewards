from django.db import migrations


def create_locations(apps, schema_editor):
    Location = apps.get_model("tides", "Location")
    Location.objects.get_or_create(
        name="Pillar Point",
        defaults=dict(
            station_id="9414131",
            latitude=37.49542392,
            longitude=-122.49865193,
            time_zone="America/Los_Angeles",
        ),
    )
    Location.objects.get_or_create(
        name="Duxbury",
        defaults=dict(
            station_id="9414958",
            latitude=37.9015078,
            longitude=-122.7211458,
            time_zone="America/Los_Angeles",
        ),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("tides", "0004_add_pillar_point"),
    ]

    operations = [
        migrations.RunPython(create_locations),
    ]
