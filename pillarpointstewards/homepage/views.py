import calendar
import datetime
import pytz
import secrets
from django.conf import settings
from django.db import connection
from django.db.models import Q
from django.contrib.postgres.aggregates import ArrayAgg
from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import get_template
from django.contrib.auth.models import User
from auth0_login.models import Auth0User
from .models import Fragment
from shifts.models import Shift
from auth0_login.utils import active_user_required


def index(request):
    upcoming_shifts = []
    contact_details = ""
    calendars = []
    user_is_inactive = False
    if request.user.is_authenticated:
        if request.user.is_active:
            _24_hours_ago = datetime.datetime.utcnow().replace(
                tzinfo=pytz.timezone("America/Los_Angeles")
            ) - datetime.timedelta(days=1)
            upcoming_shifts = list(
                request.user.shifts.filter(shift_start__gt=_24_hours_ago).order_by(
                    "shift_start"
                )
            )
            contact_details = Fragment.objects.get(slug="contact_details").fragment
            # Show calendar for next three months
            month_now = datetime.datetime.utcnow().date().replace(day=1)
            calendars = []
            for i in range(3):
                month = month_now.month + i
                year = month_now.year
                if month > 12:
                    year += 1
                    month = 1
                calendars.append(render_calendar(request, year, month))

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


def backup(request):
    secret = settings.BACKUP_SECRET
    from_header = (request.headers.get("Authorization") or "").split("Bearer ")[-1]
    if not secret or not secrets.compare_digest(secret, from_header):
        return JsonResponse(
            {"error": "Access denied - bad 'Authorization: Bearer' header"}, status=400
        )
    return JsonResponse(
        {
            "auth0_users": list(
                Auth0User.objects.values("id", "sub", "created", "user_id").order_by(
                    "id"
                )
            ),
            "users": list(
                User.objects.values(
                    "id",
                    "last_login",
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "date_joined",
                ).order_by("id")
            ),
            "shifts": list(
                Shift.objects.annotate(
                    steward_usernames=ArrayAgg(
                        "stewards__username", filter=Q(stewards__username__isnull=False)
                    )
                )
                .values(
                    "id",
                    "dawn",
                    "dusk",
                    "shift_start",
                    "shift_end",
                    "mllw_feet",
                    "lowest_tide",
                    "target_stewards",
                    "steward_usernames",
                )
                .order_by("id")
            ),
            "fragments": list(Fragment.objects.values("slug", "fragment")),
        }
    )


@active_user_required
def materials(request):
    return render(
        request,
        "materials.html",
        {"materials": Fragment.objects.get(slug="materials").fragment},
    )
