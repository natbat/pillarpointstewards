import calendar
import datetime
from django.shortcuts import render
from django.template.loader import get_template
from .models import Fragment
from shifts.models import Shift


def index(request):
    upcoming_shifts = []
    contact_details = ""
    calendars = []
    if request.user.is_authenticated:
        upcoming_shifts = list(request.user.shifts.order_by("shift_start"))
        contact_details = Fragment.objects.get(slug="contact_details").fragment
        calendars = [
            render_calendar(request, 2022, 4),
            render_calendar(request, 2022, 5),
            render_calendar(request, 2022, 6),
        ]
    return render(
        request,
        "index.html",
        {
            # TODO: upcoming only, taking timezone into account
            "upcoming_shifts": upcoming_shifts,
            "contact_details": contact_details,
            "calendars": calendars,
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
    month_start = datetime.date(year, month, 1)
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
