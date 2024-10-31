from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Forecast
from tides.models import Location
import httpx
import urllib


@csrf_exempt
def fetch_weather(request):
    if request.method == "GET":
        include_forecasts = request.GET.get("include_forecasts")
        return JsonResponse(
            {
                "locations": [
                    {
                        "location": location,
                        "forecasts": (
                            list(
                                Forecast.objects.filter(location=location["id"]).values(
                                    "date", "details"
                                )
                            )
                            if include_forecasts
                            else []
                        ),
                    }
                    for location in Location.objects.values("id", "name")
                ]
            }
        )
    api_key = request.POST.get("api_key")
    location_id = request.POST.get("location_id")
    if not (api_key and location_id):
        return JsonResponse({"error": "api_key and location_id required"})
    try:
        location = Location.objects.get(id=location_id)
    except Location.DoesNotExist:
        return JsonResponse({"error": "location not found"})
    url = "https://api.openweathermap.org/data/2.5/onecall?" + urllib.parse.urlencode(
        {
            "lat": location.latitude,
            "lon": location.longitude,
            "appid": api_key,
        }
    )
    response = httpx.get(url)
    assert response.status_code == 200
    Forecast.clear_and_create_all_from_json(location_id, response.json())
    return JsonResponse({"ok": True, "num_forecasts": Forecast.objects.count()})
