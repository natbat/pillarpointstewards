from django.contrib import admin
from .models import Forecast

admin.site.register(Forecast, list_display=["date", "location"])
