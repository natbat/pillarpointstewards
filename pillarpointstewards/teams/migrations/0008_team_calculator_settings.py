# Generated by Django 4.2.6 on 2023-11-15 03:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("teams", "0007_add_swamis"),
    ]

    operations = [
        migrations.AddField(
            model_name="team",
            name="calculator_settings",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
