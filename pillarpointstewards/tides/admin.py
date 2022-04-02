from django.contrib import admin
from .models import TidePrediction

admin.site.register(
    TidePrediction,
    list_display=("station_id", "dt", "mllw_feet"),
    readonly_fields=("station_id", "dt", "mllw_feet"),
)
