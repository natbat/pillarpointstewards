# Generated by Django 4.0.6 on 2023-10-06 19:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("teams", "0002_create_pillar_point"),
        ("shifts", "0008_secretcalendar"),
    ]

    operations = [
        migrations.AddField(
            model_name="shift",
            name="team",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="shifts",
                to="teams.team",
            ),
        ),
    ]