# Generated by Django 4.1.12 on 2024-06-21 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("teams", "0008_team_calculator_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="team",
            name="is_live",
            field=models.BooleanField(
                default=False, help_text="Is this team live on the site?"
            ),
        ),
    ]
