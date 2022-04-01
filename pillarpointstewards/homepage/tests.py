from bs4 import BeautifulSoup as Soup
from shifts.models import Shift
from django.contrib.auth.models import User
from .views import render_calendar
import datetime
import pytest
import pytz


def test_homepage(client):
    response = client.get("/")
    html = response.content.decode("utf-8")
    assert "<title>Pillar Point Tidepool Stewards</title>" in html
    assert not response.context["request"].user.is_authenticated


def test_homepage_logged_in(admin_client):
    response = admin_client.get("/")
    assert response.context["request"].user.is_authenticated
    assert response.context["upcoming_shifts"] == []


def test_homepage_shows_assigned_shifts(admin_client, admin_user_has_shift):
    response = admin_client.get("/")
    assert len(response.context["upcoming_shifts"]) == 1


def test_render_calendar(admin_client, admin_user, rf):
    # Test for just one month
    assert Shift.objects.count() == 0
    # Two other volunteers
    user1 = User.objects.create(username="one")
    user2 = User.objects.create(username="two")
    # Three shifts this month
    empty_shift = Shift.objects.create(
        dawn=make_datetime(2022, 4, 3, 6),
        dusk=make_datetime(2022, 4, 3, 20),
        shift_start=make_datetime(2022, 4, 3, 8, 30),
        shift_end=make_datetime(2022, 4, 3, 8, 30),
    )
    # Current user is on this one
    user_is_on_shift = Shift.objects.create(
        dawn=make_datetime(2022, 4, 7, 6),
        dusk=make_datetime(2022, 4, 7, 20),
        shift_start=make_datetime(2022, 4, 7, 8, 30),
        shift_end=make_datetime(2022, 4, 7, 8, 30),
    )
    user_is_on_shift.stewards.add(admin_user)
    # This one is full:
    full_shift = Shift.objects.create(
        dawn=make_datetime(2022, 4, 21, 6),
        dusk=make_datetime(2022, 4, 21, 20),
        shift_start=make_datetime(2022, 4, 21, 8, 30),
        shift_end=make_datetime(2022, 4, 21, 8, 30),
    )
    full_shift.stewards.add(user1)
    full_shift.stewards.add(user2)
    request = rf.get("/")
    request.user = admin_user
    rendered = render_calendar(request, 2022, 4)
    soup = Soup(rendered, "html.parser")
    # First tr is day headers
    trs = soup.find_all("tr")[1:]
    tds = [[(el["data-date"], el["class"]) for el in tr.find_all("td")] for tr in trs]
    assert tds == [
        [
            ("2022-03-28", ["noshift", "notcurrentmonth"]),
            ("2022-03-29", ["noshift", "notcurrentmonth"]),
            ("2022-03-30", ["noshift", "notcurrentmonth"]),
            ("2022-03-31", ["noshift", "notcurrentmonth"]),
            ("2022-04-01", ["noshift"]),
            ("2022-04-02", ["noshift", "weekend"]),
            ("2022-04-03", ["shiftday", "available", "weekend"]),
        ],
        [
            ("2022-04-04", ["noshift"]),
            ("2022-04-05", ["noshift"]),
            ("2022-04-06", ["noshift"]),
            ("2022-04-07", ["shiftday", "partfull", "yours"]),
            ("2022-04-08", ["noshift"]),
            ("2022-04-09", ["noshift", "weekend"]),
            ("2022-04-10", ["noshift", "weekend"]),
        ],
        [
            ("2022-04-11", ["noshift"]),
            ("2022-04-12", ["noshift"]),
            ("2022-04-13", ["noshift"]),
            ("2022-04-14", ["noshift"]),
            ("2022-04-15", ["noshift"]),
            ("2022-04-16", ["noshift", "weekend"]),
            ("2022-04-17", ["noshift", "weekend"]),
        ],
        [
            ("2022-04-18", ["noshift"]),
            ("2022-04-19", ["noshift"]),
            ("2022-04-20", ["noshift"]),
            ("2022-04-21", ["shiftday", "full"]),
            ("2022-04-22", ["noshift"]),
            ("2022-04-23", ["noshift", "weekend"]),
            ("2022-04-24", ["noshift", "weekend"]),
        ],
        [
            ("2022-04-25", ["noshift"]),
            ("2022-04-26", ["noshift"]),
            ("2022-04-27", ["noshift"]),
            ("2022-04-28", ["noshift"]),
            ("2022-04-29", ["noshift"]),
            ("2022-04-30", ["noshift", "weekend"]),
            ("2022-05-01", ["noshift", "weekend", "notcurrentmonth"]),
        ],
    ]


def make_datetime(yyyy, mm, dd, h, m=0, s=0):
    return datetime.datetime(
        yyyy, mm, dd, h, m, s, tzinfo=pytz.timezone("America/Los_Angeles")
    )


@pytest.mark.parametrize("path", ("/", "/patterns/"))
def test_pages_200(admin_client, path):
    assert admin_client.get(path).status_code == 200
