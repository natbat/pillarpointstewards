from shifts.models import SecretCalendar
from shifts.models import Shift
from django.contrib.auth.models import User
import json
import pytest

SHIFT = {
    "date": "April 19, 2022",
    "duration": 90,
    "minTideFeet": -1.055,
    "minTideTime": "2022-04-19T07:30:00.000Z",
    "people": 2,
    "start": "2022-04-19T07:00:00.000Z",
    "end": "2022-04-19T08:30:00.000Z",
    "dawn": "2022-04-19T06:02:00.000Z",
    "dusk": "2022-04-19T20:16:46.000Z",
}


def test_import_shifts(admin_client):
    assert Shift.objects.count() == 0
    response = admin_client.post(
        "/admin/import-shifts/",
        {"data": json.dumps([SHIFT])},
    )
    assert response.status_code == 302
    assert Shift.objects.count() == 1
    shift = Shift.objects.get()
    assert shift.shift_start.isoformat() == "2022-04-19T07:00:00+00:00"
    assert shift.shift_end.isoformat() == "2022-04-19T08:30:00+00:00"
    assert shift.dawn.isoformat() == "2022-04-19T06:02:00+00:00"
    assert shift.dusk.isoformat() == "2022-04-19T20:16:46+00:00"
    assert shift.mllw_feet == pytest.approx(-1.055)
    assert shift.lowest_tide.isoformat() == "2022-04-19T07:30:00+00:00"
    assert shift.target_stewards == 2


def test_import_shifts_update(admin_client):
    assert Shift.objects.count() == 0
    # Create a shift
    admin_client.post(
        "/admin/import-shifts/",
        {
            "data": json.dumps([SHIFT]),
        },
    )
    assert Shift.objects.count() == 1
    # Now update it by passing one on the same date with a different time
    shift_modified = dict(SHIFT, start="2022-04-19T07:15:00.000Z")
    response = admin_client.post(
        "/admin/import-shifts/",
        {
            "data": json.dumps([shift_modified]),
            "update": 1,
        },
    )
    assert response.status_code == 302
    assert Shift.objects.count() == 1
    shift = Shift.objects.get()
    assert shift.shift_start.isoformat() == "2022-04-19T07:15:00+00:00"
    assert shift.shift_end.isoformat() == "2022-04-19T08:30:00+00:00"


def test_shifts_ics_requires_key(admin_user_has_shift, client):
    response = client.get("/shifts-blah.ics")
    assert response.status_code == 400
    assert response.content == b"Wrong secret"


def test_shifts_ics(admin_user_has_shift, client, settings):
    settings.SHIFTS_ICS_SECRET = "secret"
    response = client.get("/shifts-secret.ics")
    assert response.headers["content-type"] == "text/calendar; charset=utf-8"
    assert response.content.decode("utf-8").startswith("BEGIN:VCALENDAR")


def test_personal_shifts_ics(admin_user_has_shift, admin_client):
    assert SecretCalendar.objects.count() == 0
    assert admin_client.get("/shifts-personal-1-1234.ics").status_code == 404
    # Create the secret calendar link
    assert admin_client.post("/shifts/calendar-instructions/").status_code == 302
    assert SecretCalendar.objects.count() == 1
    secret_calendar = SecretCalendar.objects.get()
    # Secret link should now return calendar
    response = admin_client.get(secret_calendar.path)
    assert response.headers["content-type"] == "text/calendar; charset=utf-8"
    assert response.content.decode("utf-8").startswith("BEGIN:VCALENDAR")
    assert b"DESCRIPTION:Shift from" in response.content


def test_edit_shift(admin_user, admin_user_in_team, admin_user_has_shift, client):
    shift = admin_user_has_shift
    # Other user should not be able to edit
    other_user = User.objects.create(username="other")
    client.force_login(other_user)
    response = client.post("/shifts/{}/edit/".format(shift.id), {"start": "blah"})
    assert response.status_code == 403
    # Admin user should be able to edit
    client.force_login(admin_user)
    response = client.post(
        "/shifts/{}/edit/".format(shift.id), {"start": "2024-01-01T13:15:00.000Z"}
    )
    assert response.status_code == 200
    shift.refresh_from_db()
    assert shift.shift_start.isoformat() == "2024-01-01T13:15:00+00:00"


def test_cancel_shift(admin_user, admin_user_in_team, admin_user_has_shift, client):
    shift = admin_user_has_shift
    # Other user should not be able to cancel
    other_user = User.objects.create(username="other")
    client.force_login(other_user)
    response = client.post("/shifts/{}/cancel/".format(shift.id), {"start": "blah"})
    assert response.status_code == 403
    # Admin user should be able to cancel
    client.force_login(admin_user)
    response = client.post(
        "/shifts/{}/cancel/".format(shift.id), {"start": "2024-01-01T13:15:00.000Z"}
    )
    assert response.status_code == 200
    assert not Shift.objects.filter(pk = shift.pk).exists()
