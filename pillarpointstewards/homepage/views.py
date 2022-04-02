import calendar
import datetime
import pytz
from django.db import connection
from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import get_template
from .models import Fragment
from shifts.models import Shift


def index(request):
    upcoming_shifts = []
    contact_details = ""
    calendars = []
    user_is_inactive = False
    if request.user.is_authenticated:
        if request.user.is_active:
            upcoming_shifts = list(request.user.shifts.order_by("shift_start"))
            contact_details = Fragment.objects.get(slug="contact_details").fragment
            calendars = [
                render_calendar(request, 2022, 4),
                render_calendar(request, 2022, 5),
                render_calendar(request, 2022, 6),
            ]
        else:
            user_is_inactive = True

    return render(
        request,
        "index.html",
        {
            # TODO: upcoming only, taking timezone into account
            "upcoming_shifts": upcoming_shifts,
            "contact_details": contact_details,
            "calendars": calendars,
            "user_is_inactive": user_is_inactive,
        },
    )


def patterns(request):
    return render(request, "patterns.html")


def next_month(month):
    if month.month == 12:
        return month.replace(month=1, year=month.year + 1)
    else:
        return month.replace(month=month.month + 1)


def render_calendar(request, year, month):
    cal = calendar.Calendar()
    month_start = datetime.datetime(
        year, month, 1, tzinfo=pytz.timezone("America/Los_Angeles")
    )
    next_month_start = next_month(month_start)
    shifts_by_date = {
        shift.shift_start.date(): shift
        for shift in Shift.objects.filter(
            shift_start__gte=month_start,
            shift_start__lt=next_month_start,
        )
    }
    weeks = []
    for days in cal.monthdatescalendar(year, month):
        week = []
        for date in days:
            classes = []
            shift = shifts_by_date.get(date)
            if shift:
                classes.append("shiftday")
                # How many people?
                count = shift.stewards.count()
                if count == 0:
                    classes.append("available")
                elif count >= 2:
                    classes.append("full")
                else:
                    classes.append("partfull")
                if shift.stewards.filter(id=request.user.id).exists():
                    classes.append("yours")
            else:
                classes.append("noshift")
            if date.weekday() in (5, 6):
                classes.append("weekend")
            if date.month != month:
                classes.append("notcurrentmonth")
            week.append(
                {
                    "date": date,
                    "classes": " ".join(classes),
                    "shift": shift,
                }
            )
        weeks.append(week)
    return get_template("calendar.html").render(
        {
            "weeks": weeks,
            "month": datetime.date(year, month, 1),
        },
        request=request,
    )


def healthcheck(request):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        SELECT
            table_name as table, array_to_json(array_agg(column_name)) as columns
        FROM
            information_schema.columns
        WHERE
            table_schema = 'public'
        GROUP BY
            table_name
        """
        )
        columns = [col[0] for col in cursor.description]
        tables = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return JsonResponse(
        {
            "tables": tables,
        }
    )
