from django.contrib import admin
from .models import TidePrediction, Location, SunriseSunset

admin.site.register(
    TidePrediction,
    list_display=("station_id", "dt", "mllw_feet"),
    list_filter=("station_id",),
    readonly_fields=("station_id", "dt", "mllw_feet"),
)

admin.site.register(
    Location,
    list_display=("name", "station_id", "time_zone", "latitude", "longitude"),
)
admin.site.register(
    SunriseSunset,
    list_display=("location", "day", "dawn", "sunrise", "noon", "sunset", "dusk"),
    list_filter=("location",),
)
