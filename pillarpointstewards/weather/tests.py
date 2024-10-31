from .models import Forecast
from tides.models import Location


WEATHER_JSON = {
    "lat": 37.4952,
    "lon": -122.5003,
    "daily": [
        {
            "dt": 1650398400,
            "sunrise": 1650374962,
            "sunset": 1650422903,
            "moonrise": 1650437100,
            "moonset": 1650381960,
            "moon_phase": 0.61,
            "temp": {
                "day": 289.25,
                "min": 284.02,
                "max": 289.25,
                "night": 284.02,
                "eve": 285.24,
                "morn": 284.31,
            },
            "feels_like": {
                "day": 288.61,
                "night": 283.43,
                "eve": 284.57,
                "morn": 283.94,
            },
            "pressure": 1019,
            "humidity": 65,
            "dew_point": 282.68,
            "wind_speed": 5.53,
            "wind_deg": 165,
            "wind_gust": 9.36,
            "weather": [
                {
                    "id": 501,
                    "main": "Rain",
                    "description": "moderate rain",
                    "icon": "10d",
                }
            ],
            "clouds": 20,
            "pop": 0.8,
            "rain": 4.28,
            "uvi": 7.21,
        },
        {
            "dt": 1650484800,
            "sunrise": 1650461282,
            "sunset": 1650509358,
            "moonrise": 0,
            "moonset": 1650471360,
            "moon_phase": 0.65,
            "temp": {
                "day": 286.41,
                "min": 283.37,
                "max": 286.73,
                "night": 285.5,
                "eve": 286.08,
                "morn": 283.47,
            },
            "feels_like": {
                "day": 285.78,
                "night": 285.35,
                "eve": 285.65,
                "morn": 282.8,
            },
            "pressure": 1015,
            "humidity": 76,
            "dew_point": 281.67,
            "wind_speed": 9.03,
            "wind_deg": 181,
            "wind_gust": 14.2,
            "weather": [
                {
                    "id": 501,
                    "main": "Rain",
                    "description": "moderate rain",
                    "icon": "10d",
                }
            ],
            "clouds": 92,
            "pop": 1,
            "rain": 4.69,
            "uvi": 7.01,
        },
    ],
    "alerts": [
        {
            "sender_name": "NWS Monterey (The San Francisco area)",
            "event": "Small Craft Advisory",
            "start": 1650492000,
            "end": 1650513600,
            "description": "...SMALL CRAFT ADVISORY REMAINS IN EFFECT FROM 3 PM TO 9 PM PDT\nWEDNESDAY...\n* WHAT...South winds 15 to 20 kt with gusts up to 25 kt\nexpected, resulting in hazardous conditions near harbor\nentrances.\n* WHERE...Coastal Waters from Point Reyes to Pigeon Point\nCalifornia out to 10 nm.\n* WHEN...From 3 PM to 9 PM PDT Wednesday.\n* IMPACTS...Conditions will be hazardous to small craft\nespecially when navigating in or near harbor entrances.",
            "tags": [],
        }
    ],
}


def test_post_to_update_weather(client, db, httpx_mock):
    httpx_mock.add_response(
        method="GET",
        json=WEATHER_JSON,
    )
    assert Forecast.objects.count() == 0
    location_id = Location.objects.first().id
    response = client.post(
        "/fetch-weather/", {"api_key": "xxx", "location_id": location_id}
    )
    assert response.status_code == 200, response.content

    # Did it hit the API?
    request = httpx_mock.get_request()
    assert (
        request.url
        == "https://api.openweathermap.org/data/2.5/onecall?lat=37.49542392&lon=-122.49865193&appid=xxx"
    )
    assert Forecast.objects.count() == 2
