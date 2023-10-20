import datetime
from dataclasses import dataclass, asdict
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import connection
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from weather.models import Forecast
from .models import Shift, ShiftChange, SecretCalendar
from .ics_utils import calendar
from auth0_login.utils import active_user_required
from homepage.models import Fragment
from tides.views import tide_times_svg_context_for_shift, tide_times_svg_context
from tides.models import Location
from teams.models import Team
from typing import Union
import json
import secrets


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = [
            "dawn",
            "dusk",
            "shift_start",
            "shift_end",
            "mllw_feet",
            "lowest_tide",
        ]


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
            "team": shift.team,
            "shift": shift,
            "user_is_on_shift": user_is_on_shift,
            "stewards": stewards,
            "contact_details": Fragment.objects.get(slug="contact_details").fragment,
            "forecast": Forecast.for_date(shift.shift_start.date()),
            "tide_times_svg": tide_times_svg_context_for_shift(shift),
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
def unassign_shift(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)
    if shift.stewards.filter(id=request.user.id).exists():
        shift.stewards.remove(request.user)
        shift.shift_changes.create(user=request.user, change="cancelled")
        return HttpResponseRedirect(f"/shifts/{shift.pk}/")
    else:
        return HttpResponse("You were not on that shift")


@active_user_required
def edit_shift(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)
    if not shift.can_edit(request.user):
        return HttpResponse("You are not allowed to edit that shift", status=403)
    if request.POST.get("start"):
        shift.shift_start = datetime.datetime.fromisoformat(request.POST["start"])
    if request.POST.get("end"):
        shift.shift_end = datetime.datetime.fromisoformat(request.POST["end"])
    shift.save()
    return HttpResponse(
        render_to_string(
            "_calculator_shift.html",
            {
                "shift": CalculatorShift.from_shift(shift),
                "team": shift.team,
                "change_times_open": True,
            },
        )
    )


@active_user_required
def cancel_shift(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)
    if not shift.can_edit(request.user):
        return HttpResponse("You are not allowed to cancel that shift", status=403)
    if request.method != "POST":
        return HttpResponse("POST only")
    details = CalculatorShift.from_shift(shift)
    shift.delete()
    details.id = None
    return HttpResponse(
        render_to_string(
            "_calculator_shift.html",
            {
                "shift": details,
                "team": shift.team,
                "shift_canceled": True,
            },
        )
    )


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
def shifts(request, program_slug):
    team = get_object_or_404(Team, slug=program_slug)
    return render(
        request,
        "shifts.html",
        {
            "team": team,
            "shifts": team.shifts.prefetch_related("stewards"),
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
    team = get_object_or_404(Team, slug=program_slug)
    # Ensure sunrise/sunset times for all locations - should really do it just for this one
    # once we have a mapping of program_slug to location
    for location in Location.objects.all():
        location.populate_sunrise_sunsets()
    return render(
        request,
        "manage_shifts.html",
        {
            "program_slug": program_slug,
            "team": team,
        },
    )


CALCULATOR_SQL = """
-- for each tide we need to know the previous/next tide to find low ones
with tides_with_previous_and_next as (
  select
    tide_predictions.dt as low_tide_datetime,
    date_trunc('day', tide_predictions.dt) as day,
    tide_predictions.mllw_feet,
    lag(tide_predictions.mllw_feet) over win as previous_mllw_feet,
    lead(tide_predictions.mllw_feet) over win as next_mllw_feet
  from
    tides_tideprediction tide_predictions
  where station_id = %(station_id)s
  window win as (
    order by tide_predictions.dt
  )
),
-- "low tides" are tides where the previous/next measurement are higher
low_tides as (
  select
    day,
    low_tide_datetime,
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
    low_tides.low_tide_datetime,
    low_tides.mllw_feet,
    tides_sunrisesunset.dawn,
    tides_sunrisesunset.sunrise,
    tides_sunrisesunset.sunset,
    tides_sunrisesunset.dusk
  from
    low_tides
    join tides_sunrisesunset on tides_sunrisesunset.day = low_tides.day
    and tides_sunrisesunset.location_id = %(location_id)s
  where
    low_tides.low_tide_datetime :: time > tides_sunrisesunset.dawn
    and low_tides.low_tide_datetime :: time < tides_sunrisesunset.dusk
),
-- now we want just the first from each day
earliest_daylight_low_tides as (
  select
    lt1.day,
    lt1.low_tide_datetime,
    lt1.mllw_feet,
    lt1.dawn,
    lt1.sunrise,
    lt1.sunset,
    lt1.dusk
  from
    low_tides_during_daylight lt1
    left join low_tides_during_daylight lt2 on lt1.day = lt2.day
    and lt1.low_tide_datetime > lt2.low_tide_datetime
  where
    -- this will be null if the day has no later tide
    lt2.low_tide_datetime is null
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


def duration_in_minutes(start: datetime.time, end: datetime.time) -> float:
    start_dt = datetime.datetime.combine(datetime.date.today(), start)
    end_dt = datetime.datetime.combine(datetime.date.today(), end)

    # Handle cases where end time is on the next day
    if end < start:
        end_dt += datetime.timedelta(days=1)

    delta = end_dt - start_dt
    return delta.total_seconds() / 60


@dataclass
class CalculatorShift:
    id: Union[int, None]
    day: datetime.date
    shift_start: datetime.time
    shift_end: datetime.time
    is_suggested: bool
    shift_model: Union[Shift, None]
    dawn: datetime.time
    dusk: datetime.time
    lowest_tide: datetime.datetime
    mllw_feet: float
    tide_times_svg: str
    html: Union[str, None]

    def shift_start_datetime(self):
        return datetime.datetime.combine(self.day, self.shift_start)

    def shift_end_datetime(self):
        return datetime.datetime.combine(self.day, self.shift_end)

    def shift_start_minus_15(self):
        return self.shift_start_datetime() - datetime.timedelta(minutes=15)

    def shift_start_plus_15(self):
        return self.shift_start_datetime() + datetime.timedelta(minutes=15)

    def shift_end_minus_15(self):
        return self.shift_end_datetime() - datetime.timedelta(minutes=15)

    def shift_end_plus_15(self):
        return self.shift_end_datetime() + datetime.timedelta(minutes=15)

    @classmethod
    def from_shift(cls, shift):
        team = shift.team
        return cls(
            id=shift.id,
            day=shift.shift_start.date(),
            shift_start=shift.shift_start.time(),
            shift_end=shift.shift_end.time(),
            is_suggested=False,
            shift_model=shift,
            dawn=shift.dawn,
            dusk=shift.dusk,
            lowest_tide=shift.lowest_tide,
            mllw_feet=shift.mllw_feet,
            tide_times_svg=tide_times_svg_context(
                date=shift.shift_start,
                shift_start=shift.shift_start,
                shift_end=shift.shift_end,
                latitude=team.location.latitude,
                longitude=team.location.longitude,
                time_zone=team.location.time_zone,
                station_id=team.location.station_id,
                low_tide_time=shift.lowest_tide,
            ),
            html="",
        )


@csrf_exempt
@active_user_required
def manage_shifts_calculator(request, program_slug):
    # Get JSON from incoming request
    data = json.loads(request.body)

    team = get_object_or_404(Team, slug=program_slug)

    shift_buffer_before = data["shift-buffer-before"]
    shift_buffer_after = data["shift-buffer-after"]
    earliest_shift_time_buffer = data["earliest-shift-time-buffer"]
    shortest_shift_duration = data["shortest-shift-duration"]

    with connection.cursor() as cursor:
        cursor.execute(
            CALCULATOR_SQL,
            {
                "tide_weekday": data["weekday-low-tide"],
                "tide_weekend": data["weekend-low-tide"],
                "location_id": team.location.id,
                "station_id": team.location.station_id,
            },
        )
        column_names = [col[0] for col in cursor.description]
        # Convert the results into a list of dictionaries
        results = [dict(zip(column_names, row)) for row in cursor.fetchall()]

    calculator_shifts = [
        CalculatorShift.from_shift(shift)
        for shift in team.shifts.filter(shift_start__gte=datetime.datetime.now())
    ]

    # Avoid suggesting duplicates based on exact start/end
    existing_shifts = set(
        (shift.shift_start_datetime(), shift.shift_end_datetime())
        for shift in calculator_shifts
    )

    # Add "start" and "end" field to each result and append to calculator_shifts
    for tide in results:
        low_tide_dt = tide["low_tide_datetime"]
        new_start = low_tide_dt - datetime.timedelta(hours=shift_buffer_before)
        new_end = low_tide_dt + datetime.timedelta(hours=shift_buffer_after)
        dawn = datetime.datetime.combine(tide["day"], tide["dawn"], datetime.UTC)
        dusk = datetime.datetime.combine(tide["day"], tide["dusk"], datetime.UTC)
        pretend_dawn = dawn + datetime.timedelta(hours=earliest_shift_time_buffer)

        if pretend_dawn > new_start:
            new_start = pretend_dawn
        if dusk < new_end:
            new_end = dusk

        tide["start_not_rounded"] = new_start.time()
        tide["start"] = round_to_fifteen_minutes(new_start).time()
        tide["end_not_rounded"] = new_end.time()
        tide["end"] = round_to_fifteen_minutes(new_end).time()

        shift_start = datetime.datetime.combine(tide["day"], tide["start"])
        shift_end = datetime.datetime.combine(tide["day"], tide["end"])

        if (shift_start, shift_end) in existing_shifts:
            continue

        tide["tide_times_svg"] = tide_times_svg_context(
            date=tide["day"],
            shift_start=shift_start,
            shift_end=shift_end,
            latitude=team.location.latitude,
            longitude=team.location.longitude,
            time_zone=team.location.time_zone,
            station_id=team.location.station_id,
            low_tide_time=tide["low_tide_datetime"],
        )
        # Filter out the shifts that are too short
        if duration_in_minutes(tide["start"], tide["end"]) <= shortest_shift_duration:
            continue
        calculator_shifts.append(
            CalculatorShift(
                id=None,
                day=tide["day"].date(),
                shift_start=tide["start"],
                shift_end=tide["end"],
                is_suggested=True,
                shift_model=None,
                dawn=tide["dawn"],
                dusk=tide["dusk"],
                lowest_tide=tide["low_tide_datetime"],
                mllw_feet=tide["mllw_feet"],
                tide_times_svg=tide["tide_times_svg"],
                html=None,
            )
        )

    calculator_shifts.sort(key=lambda s: (s.day, s.shift_start))

    results = calculator_shifts

    def as_datetime(day, time):
        if isinstance(time, datetime.datetime):
            return time.isoformat()
        return datetime.datetime.combine(day, time).isoformat()

    # Add rendered HTML fragment to each one
    for result in results:
        result.html = render_to_string(
            "_calculator_shift.html",
            {
                "shift": result,
                "team": team,
                "post_vars": {
                    "shift_start": as_datetime(result.day, result.shift_start),
                    "shift_end": as_datetime(result.day, result.shift_end),
                    "lowest_tide": result.lowest_tide.isoformat(),
                    "mllw_feet": result.mllw_feet,
                    "dawn": as_datetime(result.day, result.dawn),
                    "dusk": as_datetime(result.day, result.dusk),
                },
            },
        )
    # Can't calculate this yet, because we are missing the logic that figures out
    # the actual start and end time of each shift
    average_shift_length = None

    return HttpResponse(
        json.dumps(
            {
                "input": data,
                "results": [asdict(r) for r in results],
                "top_block": render_to_string(
                    "_calculator_top_block.html",
                    {
                        # TODO: Should this be future only?
                        "num_confirmed_shifts": team.shifts.count(),
                        "num_suggested_shifts": len(results),
                        "num_combined_shifts": team.shifts.count() + len(results),
                        "average_shift_length": average_shift_length,
                    },
                ),
            },
            default=str,
        ),
        content_type="application/json",
    )


def add_shift(request, program_slug):
    team = get_object_or_404(Team, slug=program_slug)
    if request.method == "POST":
        form = ShiftForm(request.POST)
        if not form.is_valid():
            return HttpResponse("Invalid submission: " + str(form.errors))
        shift = form.save(commit=False)
        shift.team = team
        shift.save()
        # Render the new shift and return that fragment
        return HttpResponse(
            render_to_string(
                "_calculator_shift.html",
                {
                    "shift": CalculatorShift.from_shift(shift),
                    "team": team,
                },
            )
        )
    return HttpResponse("POST only")


def round_to_fifteen_minutes(dt):
    fifteen_minutes = datetime.timedelta(minutes=15)
    dt_min = datetime.datetime.min.replace(tzinfo=datetime.UTC)
    total_seconds = (dt - dt_min).total_seconds()
    rounded_seconds = (
        round(total_seconds / fifteen_minutes.total_seconds())
        * fifteen_minutes.total_seconds()
    )
    return dt_min + datetime.timedelta(seconds=rounded_seconds)
