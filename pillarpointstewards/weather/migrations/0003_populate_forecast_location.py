from django.db import migrations


def add_data_forward(apps, schema_editor):
    Forecast = apps.get_model("weather", "Forecast")
    Location = apps.get_model("tides", "Location")
    location = Location.objects.get(name="Pillar Point")
    Forecast.objects.update(location=location)


class Migration(migrations.Migration):

    dependencies = [
        ("weather", "0002_forecast_location"),
        ("tides", "0005_populate_tide_locations"),
    ]

    operations = [migrations.RunPython(add_data_forward)]
