from astral import LocationInfo, sun
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Count
from django.conf import settings
import secrets
from datetime import timezone
import datetime
import time
import pytz
from .models import TidePrediction
from shifts.models import Shift


def time_to_float(s):
    if s.count(":") == 2:
        hh, mm, ss = map(float, s.split(":"))
    else:
        hh, mm = map(float, s.split(":"))
        ss = 0.0
    # 1 hour = 1/24th, 1 minute = 60th/hour, 1 second = 60th/minute
    return hh / 24 + ((mm / 60) * (1 / 24)) + ((ss / 60) * (1 / 24 / 60))


def tide_times_svg_context_for_shift(shift):
    date = shift.shift_start.replace(hour=0, minute=0, second=0)
    shift_start = shift.shift_start
    shift_end = shift.shift_end
    latitude = shift.team.location.latitude
    longitude = shift.team.location.longitude
    time_zone = shift.team.location.time_zone
    station_id = shift.team.location.station_id
    low_tide_time = shift.lowest_tide
    return tide_times_svg_context(
        date,
        shift_start,
        shift_end,
        latitude,
        longitude,
        time_zone,
        station_id,
        low_tide_time,
    )


def tide_times_svg_context(
    date,
    shift_start,
    shift_end,
    latitude,
    longitude,
    time_zone,
    station_id,
    low_tide_time,
):
    date = date.replace(hour=0, minute=0, second=0)
    predictions = list(
        TidePrediction.objects.filter(
            station_id=station_id,
            dt__gte=date,
            dt__lt=date + datetime.timedelta(days=1),
        ).values()
    )

    if not predictions:
        return None

    heights = [
        {
            "time": prediction["dt"].time().isoformat(),
            "time_pct": round(
                100 * time_to_float(prediction["dt"].time().isoformat()), 2
            ),
            "feet": prediction["mllw_feet"],
        }
        for prediction in predictions
    ]
    min_feet = min(h["feet"] for h in heights[1:-1])
    max_feet = max(h["feet"] for h in heights[1:-1])
    feet_delta = max_feet - min_feet
    svg_points = []
    for i, height in enumerate(heights[1:-1]):
        ratio = (height["feet"] - min_feet) / feet_delta
        line_height_pct = 100 - (ratio * 100)
        svg_points.append((i, line_height_pct))

    location_info = LocationInfo(
        latitude=latitude,
        longitude=longitude,
        timezone=time_zone,
    )
    astral_info = sun.sun(location_info.observer, date=date)
    tz = pytz.timezone(time_zone)

    astral_pcts = {
        "{}_pct".format(key): round(
            100
            * time_to_float(value.astimezone(tz).time().isoformat(timespec="seconds")),
            2,
        )
        for key, value in astral_info.items()
    }

    context = {
        "date": date,
        "heights": heights,
        "predictions": predictions,
        "svg_points": " ".join("{},{:.2f}".format(i, pct) for i, pct in svg_points),
        "astral": astral_pcts,
    }

    shift_start_pct = round(100 * time_to_float(shift_start.time().isoformat()), 2)
    context["shift_start"] = shift_start
    context["shift_start_pct"] = shift_start_pct
    context["shift_end"] = shift_end
    context["shift_width_pct"] = (
        round(100 * time_to_float(shift_end.time().isoformat()), 2) - shift_start_pct
    )

    if low_tide_time:
        context["low_tide_time"] = low_tide_time
        context["low_tide_time_pct"] = round(
            100 * time_to_float(low_tide_time.time().isoformat()), 2
        )

    return context


def debug(request, date):
    yyyy, mm, dd = date.split("-")
    day_start = datetime.datetime(int(yyyy), int(mm), int(dd), tzinfo=timezone.utc)
    return render(
        request,
        "tide-times-debug.html",
        {
            "tide_times_svg": tide_times_svg_context_for_date(
                day_start.replace(hour=0, minute=0, second=0)
            )
        },
    )


def debug_just_svg(request, date):
    yyyy, mm, dd = date.split("-")
    day_start = datetime.datetime(int(yyyy), int(mm), int(dd), tzinfo=timezone.utc)
    return render(
        request,
        "_tide_svg.html",
        {
            "tide_times_svg": tide_times_svg_context_for_date(
                day_start.replace(hour=0, minute=0, second=0)
            )
        },
    )


@csrf_exempt
def update_all_stations(request):
    secret = settings.BACKUP_SECRET
    from_header = (request.headers.get("Authorization") or "").split("Bearer ")[-1]
    if not secret or not secrets.compare_digest(secret, from_header):
        return JsonResponse(
            {"error": "Access denied - bad 'Authorization: Bearer' header"}, status=400
        )

    def counts():
        station_counts = (
            TidePrediction.objects.values("station_id")
            .annotate(count=Count("id"))
            .order_by("station_id")
            .values("station_id", "count")
        )
        return {str(item["station_id"]): item["count"] for item in station_counts}

    if request.method == "POST":
        before = counts()
        start = time.time()
        TidePrediction.update_all_stations()
        end = time.time()
        after = counts()
        return JsonResponse(
            {"ok": True, "before": before, "after": after, "seconds": end - start}
        )
    else:
        return JsonResponse({"counts": counts()})
