from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static

import django_sql_dashboard

from homepage import views as homepage
from shifts import views as shifts
from auth0_login import views as auth0_login
from tides import views as tides
from weather import views as weather


def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path("", homepage.index),
    path("join-program/", homepage.join_program),
    path("login/", auth0_login.login),
    path("signup/", auth0_login.signup),
    path("logout/", auth0_login.logout),
    path("auth0-callback/", auth0_login.callback),
    path("healthcheck/", homepage.healthcheck),
    path("backup.json", homepage.backup),
    path("shifts/<int:shift_id>/", shifts.shift),
    path("cancel-shift/<int:shift_id>/", shifts.cancel_shift),
    path("assign-shift/<int:shift_id>/", shifts.assign_shift),
    path("shifts/", shifts.shifts),
    path("materials/", homepage.materials),
    path("shifts/calendar-instructions/", shifts.calendar_instructions),
    path("shifts-personal-<int:id>-<str:key>.ics", shifts.shifts_ics_personal),
    path("shifts-<str:key>.ics", shifts.shifts_ics),
    path("fetch-weather/", weather.fetch_weather),
    path("patterns/", homepage.patterns),
    path("admin/import-shifts/", shifts.import_shifts),
    path("admin/timeline/", shifts.timeline),
    path("admin/", admin.site.urls),
    path("dashboard/", include(django_sql_dashboard.urls)),
    path("sentry-debug/", trigger_error),
    path("debug/tide-times/<str:date>/", tides.debug),
    path("debug/tide-times-just-svg/<str:date>/", tides.debug_just_svg),
    # /programs/ pages to support multiple programs
    path("programs/<str:program_slug>/", homepage.program_index),
    path("programs/<str:program_slug>/manage-shifts/", shifts.manage_shifts),
    path(
        "programs/<str:program_slug>/manage-shifts/calculator/",
        shifts.manage_shifts_calculator,
    ),
    path("programs/<str:program_slug>/add-shift/", shifts.add_shift),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
