from astral import LocationInfo, sun
from django.shortcuts import render
from django.utils import timezone
import datetime
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


def debug(request, date):
    yyyy, mm, dd = date.split("-")
    day_start = datetime.datetime(int(yyyy), int(mm), int(dd), tzinfo=timezone.utc)

    predictions = list(
        TidePrediction.objects.filter(
            dt__gte=day_start, dt__lt=day_start + datetime.timedelta(hours=24)
        ).values()
    )

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
        latitude=37.495182, longitude=-122.5003437, timezone="America/Los_Angeles"
    )
    astral_info = sun.sun(location_info.observer, date=day_start.date())
    tz = pytz.timezone("America/Los_Angeles")

    astral_pcts = {
        "{}_pct".format(key): round(
            100
            * time_to_float(value.astimezone(tz).time().isoformat(timespec="seconds")),
            2,
        )
        for key, value in astral_info.items()
    }

    context = {
        "date": day_start.date(),
        "heights": heights,
        "predictions": predictions,
        "svg_points": " ".join("{},{:.2f}".format(i, pct) for i, pct in svg_points),
        "astral": astral_pcts,
    }

    try:
        shift = Shift.objects.get(shift_start__date=day_start.date())
        shift_start_pct = round(
            100 * time_to_float(shift.shift_start.time().isoformat()), 2
        )
        context["shift"] = shift
        context["shift_start_pct"] = shift_start_pct
        context["shift_width_pct"] = (
            round(100 * time_to_float(shift.shift_end.time().isoformat()), 2)
            - shift_start_pct
        )
    except Shift.DoesNotExist:
        shift = None

    if shift and shift.lowest_tide:
        context["low_tide_time"] = shift.lowest_tide
        context["low_tide_time_pct"] = round(
            100 * time_to_float(shift.lowest_tide.time().isoformat()), 2
        )

    return render(request, "tide-times-debug.html", context)
