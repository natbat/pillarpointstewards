from django.db import migrations


def add_active_users_to_pillar_point(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Team = apps.get_model("teams", "Team")
    Membership = apps.get_model("teams", "Membership")
    team = Team.objects.get(slug="pillar-point")
    for user in User.objects.filter(is_active=True):
        Membership.objects.get_or_create(user=user, team=team)


class Migration(migrations.Migration):
    dependencies = [
        ("teams", "0002_create_pillar_point"),
    ]

    operations = [
        migrations.RunPython(add_active_users_to_pillar_point),
    ]
