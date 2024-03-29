# Generated by Django 4.2.6 on 2023-10-06 21:51

from django.db import migrations, models
import django.db.models.deletion
import teams.models


class Migration(migrations.Migration):
    dependencies = [
        ("teams", "0003_add_active_users_to_pillar_point"),
    ]

    operations = [
        migrations.CreateModel(
            name="TeamInviteCode",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        default=teams.models.generate_code, max_length=6, unique=True
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "team",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="codes",
                        to="teams.team",
                    ),
                ),
            ],
        ),
    ]
