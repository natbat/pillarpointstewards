from django.db import migrations


def set_is_live(apps, schema_editor):
    Team = apps.get_model("teams", "Team")
    Team.objects.filter(slug__in=("pillar-point", "duxbury")).update(is_live=True)


class Migration(migrations.Migration):

    dependencies = [
        ("teams", "0009_team_is_live"),
    ]

    operations = [migrations.RunPython(set_is_live)]
