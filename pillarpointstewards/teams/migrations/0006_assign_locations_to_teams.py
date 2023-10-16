from django.db import migrations


def assign_locations(apps, schema_editor):
    Team = apps.get_model("teams", "Team")
    Location = apps.get_model("tides", "Location")
    pillar_point_location = Location.objects.get(name="Pillar Point")
    pillar_point_team = Team.objects.get(slug="pillar-point")
    pillar_point_team.location = pillar_point_location
    pillar_point_team.save()
    duxbury_team = Team.objects.get_or_create(
        slug="duxbury",
        defaults=dict(
            name="Duxbury",
        ),
    )[0]
    duxbury_team.location = Location.objects.get(name="Duxbury")
    duxbury_team.save()


class Migration(migrations.Migration):
    dependencies = [
        ("teams", "0005_team_location"),
        ("tides", "0005_populate_tide_locations"),
    ]

    operations = [
        migrations.RunPython(assign_locations),
    ]
