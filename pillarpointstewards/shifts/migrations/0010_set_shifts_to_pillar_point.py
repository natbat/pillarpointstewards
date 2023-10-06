from django.db import migrations


def set_shifts_to_pillar_point(apps, schema_editor):
    Shift = apps.get_model("shifts", "Shift")
    Team = apps.get_model("teams", "Team")
    pillar_point = Team.objects.get(slug="pillar-point")
    Shift.objects.update(team=pillar_point)


class Migration(migrations.Migration):
    dependencies = [
        ("shifts", "0009_shift_team"),
    ]

    operations = [
        migrations.RunPython(set_shifts_to_pillar_point),
    ]
