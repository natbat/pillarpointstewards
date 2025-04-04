from calendar import c
from django.db import models
from tides.models import Location
import datetime


class Forecast(models.Model):
    date = models.DateField(db_index=True)
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="forecasts",
        blank=True,
        null=True,
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    details = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Weather on {}".format(self.date)

    @classmethod
    def create_from_json(cls, location_id, data, latitude, longitude):
        # Warning: dt is 00:00 in UTC at that location:
        # "dt": 1649091600
        # So need to use that to figure out the date
        date = datetime.datetime.utcfromtimestamp(data["dt"]).strftime("%Y-%m-%d")
        return cls.objects.create(
            date=date,
            location_id=location_id,
            latitude=latitude,
            longitude=longitude,
            details=data,
        )

    @classmethod
    def for_date(cls, location_id, date):
        matches = list(cls.objects.filter(location_id=location_id, date=date))
        if matches:
            return matches[0]
        else:
            return None

    @classmethod
    def create_all_from_json(cls, location_id, data):
        longitude = data["lon"]
        latitude = data["lat"]
        for record in data["daily"]:
            cls.create_from_json(
                location_id, record, latitude=latitude, longitude=longitude
            )

    @classmethod
    def clear_and_create_all_from_json(cls, location_id, data):
        cls.objects.filter(location_id=location_id).delete()
        cls.create_all_from_json(location_id, data)
