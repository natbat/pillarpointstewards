# Generated by Django 4.2.6 on 2023-10-21 00:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("shifts", "0011_alter_shift_dawn_alter_shift_dusk"),
    ]

    operations = [
        migrations.AddField(
            model_name="shift",
            name="description",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
