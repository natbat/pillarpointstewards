from django.db import models
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from urllib.parse import urlencode
import datetime
import httpx


class TidePrediction(models.Model):
    station_id = models.IntegerField(db_index=True)
    dt = models.DateTimeField(
        help_text="America/Los_Angeles time even though it looks like UTC"
    )
    mllw_feet = models.FloatField()

    def __str__(self):
        return "{} at {}".format(self.mllw_feet, self.dt)

    @classmethod
    def populate_for_station(cls, station_id):
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        end_date = yesterday + datetime.timedelta(days=365)
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
        data = httpx.get(url).json()
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
