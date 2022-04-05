"""pillarpointstewards URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from homepage import views as homepage
from shifts import views as shifts
from auth0_login import views as auth0_login
from tides import views as tides


def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path("", homepage.index),
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
    path("shifts-<str:key>.ics", shifts.shifts_ics),
    path("signup/<int:id>-<str:key>/", auth0_login.secret_signup),
    path("patterns/", homepage.patterns),
    path("admin/import-shifts/", shifts.import_shifts),
    path("admin/timeline/", shifts.timeline),
    path("admin/", admin.site.urls),
    path("sentry-debug/", trigger_error),
    path("debug/tide-times/<str:date>/", tides.debug),
    path("debug/tide-times-just-svg/<str:date>/", tides.debug_just_svg),
]
