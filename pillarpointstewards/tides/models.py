from astral import LocationInfo, sun
from django.db import models
from django.utils.dateparse import parse_datetime
from datetime import timezone
from urllib.parse import urlencode
import datetime
import httpx
import pytz


class TidePrediction(models.Model):
    station_id = models.IntegerField(db_index=True)
    dt = models.DateTimeField(
        help_text="America/Los_Angeles time even though it looks like UTC"
    )
    mllw_feet = models.FloatField()

    def __str__(self):
        return "{} at {}".format(self.mllw_feet, self.dt)

    class Meta:
        unique_together = ("station_id", "dt")

    @classmethod
    def populate_for_station(cls, station_id):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        end_date = yesterday + datetime.timedelta(days=180)
        url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?" + urlencode(
            {
                "begin_date": yesterday.strftime("%Y%m%d"),
                "end_date": end_date.strftime("%Y%m%d"),
                "product": "predictions",
                "station": station_id,
                "datum": "mllw",
                "time_zone": "lst_ldt",
                "units": "english",
                "format": "json",
            }
        )
        data = httpx.get(url, timeout=30).json()
        cls.populate_from_data(station_id, data)

    @classmethod
    def populate_from_data(cls, station_id, data):
        cls.objects.bulk_create(
            [
                cls(
                    station_id=station_id,
                    dt=parse_datetime(p["t"]).replace(tzinfo=timezone.utc),
                    mllw_feet=float(p["v"]),
                )
                for p in data["predictions"]
            ],
            ignore_conflicts=True,
            batch_size=1000,
        )


class Location(models.Model):
    name = models.CharField(max_length=255)
    station_id = models.IntegerField(null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    time_zone = models.CharField(max_length=50)

    def populate_sunrise_sunsets(self):
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=365)

        # First, check the days for which we already have sunrise and sunset data
        existing_days = set(self.sunrise_sunsets.values_list("day", flat=True))

        # Then determine the days for which we need the data
        missing_days = [
            today + datetime.timedelta(days=i)
            for i in range((end_date - today).days)
            if today + datetime.timedelta(days=i) not in existing_days
        ]

        location_info = LocationInfo(
            self.name, "", self.time_zone, self.latitude, self.longitude
        )
        tz = pytz.timezone(self.time_zone)

        for day in missing_days:
            info = sun.sun(location_info.observer, date=day)

            # Create and save SunriseSunset instance
            sunrise_sunset = SunriseSunset(location=self, day=day)
            for key, value in info.items():
                setattr(sunrise_sunset, key, value.astimezone(tz).time())
            sunrise_sunset.save()

    def __str__(self):
        return self.name


class SunriseSunset(models.Model):
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="sunrise_sunsets"
    )
    day = models.DateField()
    dawn = models.TimeField()
    sunrise = models.TimeField()
    noon = models.TimeField()
    sunset = models.TimeField()
    dusk = models.TimeField()

    class Meta:
        unique_together = ("location", "day")

    def __str__(self):
        return f"{self.location.name} - {self.day}"
