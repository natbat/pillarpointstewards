from django.db import migrations


def add_pillar_point(apps, schema_editor):
    Team = apps.get_model("teams", "Team")
    if not Team.objects.filter(slug="pillar-point").exists():
        Team.objects.create(name="Pillar Point", slug="pillar-point")


class Migration(migrations.Migration):
    dependencies = [
        ("teams", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_pillar_point),
    ]
