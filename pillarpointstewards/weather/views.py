from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Forecast
import httpx
import urllib


@csrf_exempt
def fetch_weather(request):
    api_key = request.POST.get("api_key")
    assert api_key
    url = "https://api.openweathermap.org/data/2.5/onecall?" + urllib.parse.urlencode(
        {
            "lat": 37.495182,
            "lon": -122.5003437,
            "appid": api_key,
        }
    )
    response = httpx.get(url)
    assert response.status_code == 200
    Forecast.clear_and_create_all_from_json(response.json())
    return JsonResponse({"ok": True, "num_forecasts": Forecast.objects.count()})
