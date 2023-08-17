from curses.ascii import HT
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import connection
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from weather.models import Forecast
from .models import Shift, ShiftChange, SecretCalendar
from .ics_utils import calendar
from auth0_login.utils import active_user_required
from homepage.models import Fragment
from tides.views import tide_times_svg_context_for_date
from tides.models import Location
import json
import secrets


@active_user_required
def shift(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)
    user_is_on_shift = shift.stewards.filter(id=request.user.id).exists()
    stewards = list(shift.stewards.all())
    # Ensure current user is at the bottom, if they are a steward
    if user_is_on_shift:
        stewards = [s for s in stewards if s != request.user] + [request.user]

    return render(
        request,
        "shift.html",
        {
            "shift": shift,
            "user_is_on_shift": user_is_on_shift,
            "stewards": stewards,
            "contact_details": Fragment.objects.get(slug="contact_details").fragment,
            "forecast": Forecast.for_date(shift.shift_start.date()),
            "tide_times_svg": tide_times_svg_context_for_date(
                shift.shift_start.replace(hour=0, minute=0, second=0)
            ),
        },
    )


@staff_member_required
def import_shifts(request):
    data = request.POST.get("data")
    update = bool(request.POST.get("update"))
    if data:
        shifts = json.loads(data)
        for shift in shifts:
            if update:
                # Is there an existing shift on this day?
                try:
                    existing_shift = Shift.objects.get(
                        shift_start__date=shift["start"].split("T")[0]
                    )
                    existing_shift.shift_start = shift["start"]
                    existing_shift.shift_end = shift["end"]
                    existing_shift.dawn = shift["dawn"]
                    existing_shift.dusk = shift["dusk"]
                    existing_shift.mllw_feet = shift["minTideFeet"]
                    existing_shift.lowest_tide = shift["minTideTime"]
                    existing_shift.target_stewards = shift["people"]
                    existing_shift.save()
                    continue
                except Shift.DoesNotExist:
                    pass
            Shift.objects.get_or_create(
                shift_start=shift["start"],
                shift_end=shift["end"],
                defaults={
                    "dawn": shift["dawn"],
                    "dusk": shift["dusk"],
                    "mllw_feet": shift["minTideFeet"],
                    "lowest_tide": shift["minTideTime"],
                    "target_stewards": shift["people"],
                },
            )
        return HttpResponseRedirect("/admin/shifts/shift/")

    return render(request, "import_shifts.html")


@active_user_required
def cancel_shift(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)
    if shift.stewards.filter(id=request.user.id).exists():
        shift.stewards.remove(request.user)
        shift.shift_changes.create(user=request.user, change="cancelled")
        return HttpResponseRedirect(f"/shifts/{shift.pk}/")
    else:
        return HttpResponse("You were not on that shift")


@active_user_required
def assign_shift(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)
    if not shift.stewards.filter(id=request.user.id).exists():
        shift.stewards.add(request.user)
        shift.shift_changes.create(user=request.user, change="assigned")
        return HttpResponseRedirect(f"/shifts/{shift.pk}/")
    else:
        return HttpResponse("You were already on that shift")


@staff_member_required
def timeline(request):
    return render(
        request,
        "timeline.html",
        {
            "shift_changes": ShiftChange.objects.select_related(
                "shift", "user"
            ).order_by("-when")[:200],
        },
    )


@active_user_required
def shifts(request):
    return render(
        request,
        "shifts.html",
        {
            "shifts": Shift.objects.prefetch_related("stewards"),
        },
    )


def shifts_ics(request, key):
    if not settings.SHIFTS_ICS_SECRET or not secrets.compare_digest(
        key, settings.SHIFTS_ICS_SECRET
    ):
        return HttpResponse("Wrong secret", status=400)
    return render_calendar(
        request,
        Shift.objects.prefetch_related("stewards"),
        title="Pillar Point Stewards, all shifts",
    )


def render_calendar(request, shifts, title):
    def description(shift):
        stewards = ", ".join(shift.stewards.values_list("username", flat=True))
        stewards = (
            "Stewards: {}".format(stewards) if stewards else "No stewards signed up yet"
        )
        lines = [
            f"Shift from {shift.shift_start.time()} to {shift.shift_end.time()}",
            stewards,
        ]
        if shift.mllw_feet:
            lines.append(f"Low tide {shift.mllw_feet}ft at {shift.lowest_tide}")
        lines.append(f"https://www.pillarpointstewards.com/shifts/{shift.id}/")
        return "\n\n".join(lines)

    shifts = [
        {
            "name": "Steward shift at Pillar Point",
            "dtstart": shift.shift_start.isoformat().rstrip("Z"),
            "dtend": shift.shift_end.isoformat().rstrip("Z"),
            "description": description(shift),
            "tzid": "America/Los_Angeles",
            "id": str(shift.id),
        }
        for shift in shifts
    ]
    s = calendar(shifts, title=title)
    content_type = "text/calendar; charset=utf-8"
    if request.GET.get("_plain"):
        content_type = "text/plain; charset=utf-8"

    return HttpResponse(s, content_type=content_type)


def shifts_ics_personal(request, id, key):
    secret_calendar = get_object_or_404(SecretCalendar, pk=id)
    if not secrets.compare_digest(key, secret_calendar.secret):
        return HttpResponse("Wrong secret", status=400)

    return render_calendar(
        request,
        Shift.objects.filter(stewards=secret_calendar.user).prefetch_related(
            "stewards"
        ),
        title="{} shifts for Pillar Point Stewards".format(
            secret_calendar.user.get_full_name() or secret_calendar.user.username
        ),
    )


@active_user_required
def calendar_instructions(request):
    secret_calendar = None
    try:
        secret_calendar = request.user.secret_calendar
    except SecretCalendar.DoesNotExist:
        pass
    if request.method == "POST":
        # Create secret calendar link if it does not exist and redirect
        if not secret_calendar:
            SecretCalendar.objects.create(user=request.user)
        return HttpResponseRedirect(request.path)
    return render(
        request,
        "calendar_instructions.html",
        {"secret_calendar": secret_calendar},
    )


@active_user_required
def manage_shifts(request, program_slug):
    # Ensure sunrise/sunset times for all locations - should really do it just for this one
    # once we have a mapping of program_slug to location
    for location in Location.objects.all():
        location.populate_sunrise_sunsets()
    return render(
        request,
        "manage_shifts.html",
        {
            "program_slug": program_slug,
        },
    )


CALCULATOR_SQL = """
-- for each tide we need to know the previous/next tide to find low ones
with tides_with_previous_and_next as (
  select
    tide_predictions.dt as datetime,
    date_trunc('day', tide_predictions.dt) as day,
    tide_predictions.mllw_feet,
    lag(tide_predictions.mllw_feet) over win as previous_mllw_feet,
    lead(tide_predictions.mllw_feet) over win as next_mllw_feet
  from
    tides_tideprediction tide_predictions
  window win as (
      order by
        tide_predictions.dt
    )
),
-- "low tides" are tides where the previous/next measurement are higher
low_tides as (
  select
    day,
    datetime,
    mllw_feet
  from
    tides_with_previous_and_next
  where
    previous_mllw_feet is not null
    and next_mllw_feet is not null
    and mllw_feet <= previous_mllw_feet
    and mllw_feet <= next_mllw_feet
),
-- but we only want to know about low tides during daylight hours
low_tides_during_daylight as (
  select
    low_tides.day,
    low_tides.datetime,
    low_tides.mllw_feet,
    tides_sunrisesunset.dawn,
    tides_sunrisesunset.sunrise,
    tides_sunrisesunset.sunset,
    tides_sunrisesunset.dusk
  from
    low_tides
    join tides_sunrisesunset on tides_sunrisesunset.day = low_tides.day
    and tides_sunrisesunset.location_id = 1
  where
    low_tides.datetime :: time > tides_sunrisesunset.dawn
    and low_tides.datetime :: time < tides_sunrisesunset.dusk
),
-- now we want just the first from each day
earliest_daylight_low_tides as (
  select
    lt1.day,
    lt1.datetime,
    lt1.mllw_feet,
    lt1.dawn,
    lt1.sunrise,
    lt1.sunset,
    lt1.dusk
  from
    low_tides_during_daylight lt1
    left join low_tides_during_daylight lt2 on lt1.day = lt2.day
    and lt1.datetime > lt2.datetime
  where
    -- this will be null if the day has no later tide
    lt2.datetime is null
)
-- and finally, filter based on tide_weekday and tide_weekend inputs
select
  *
from
  earliest_daylight_low_tides
where
  case
    when extract(
      dow
      from
        day
    ) in (0, 6) then mllw_feet < %(tide_weekend)s
    else mllw_feet < %(tide_weekday)s
  end
"""


@csrf_exempt
@active_user_required
def manage_shifts_calculator(request, program_slug):
    # Get JSON from incoming request
    data = json.loads(request.body)

    with connection.cursor() as cursor:
        cursor.execute(
            CALCULATOR_SQL,
            {
                "tide_weekday": data["weekday-low-tide"],
                "tide_weekend": data["weekend-low-tide"],
            },
        )
        column_names = [col[0] for col in cursor.description]

        # Convert the results into a list of dictionaries
        results = [dict(zip(column_names, row)) for row in cursor.fetchall()]

    return HttpResponse(
        json.dumps(
            {
                "input": data,
                "results": results,
            },
            default=str,
        ),
        content_type="application/json",
    )
