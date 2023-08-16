from django.contrib import admin
from .models import TidePrediction, Location, SunriseSunset

admin.site.register(
    TidePrediction,
    list_display=("station_id", "dt", "mllw_feet"),
    readonly_fields=("station_id", "dt", "mllw_feet"),
)

admin.site.register(Location)
admin.site.register(
    SunriseSunset,
    list_display=("location", "day", "dawn", "sunrise", "noon", "sunset", "dusk"),
)
