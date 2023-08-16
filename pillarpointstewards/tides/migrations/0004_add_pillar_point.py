from django.db import migrations


def add_pillar_point(apps, schema_editor):
    Location = apps.get_model("tides", "Location")
    Location.objects.create(
        name="Pillar Point",
        station_id=9414131,
        latitude=37.49542392,
        longitude=-122.49865193,
        time_zone="America/Los_Angeles",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("tides", "0003_location_sunrisesunset"),
    ]

    operations = [
        migrations.RunPython(add_pillar_point),
    ]
