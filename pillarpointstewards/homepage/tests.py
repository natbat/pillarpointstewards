from bs4 import BeautifulSoup as Soup
from shifts.models import Shift
from django.contrib.auth.models import User
from .views import render_calendar
from teams.models import Team, TeamInviteCode
import datetime
import pytest
import pytz


def test_homepage(client):
    response = client.get("/")
    html = response.content.decode("utf-8")
    assert "Tidepool Stewards</title>" in html
    assert not response.context["request"].user.is_authenticated


@pytest.mark.parametrize("scenario", ("no-teams", "one-team", "two-teams"))
def test_homepage_logged_in(django_user_model, client, scenario):
    user = django_user_model(username="testuser")
    user.is_active = True
    user.save()
    if scenario != "no-teams":
        user.teams.add(Team.objects.get(slug="pillar-point"))
    if scenario == "two-teams":
        user.teams.add(Team.objects.get(slug="duxbury"))
    client.force_login(user)
    response = client.get("/")
    if scenario == "one-team":
        assert response.status_code == 302
        assert response.url == "/programs/pillar-point/"
    elif scenario == "two-teams":
        # They should get to pick
        assert response.status_code == 200
        html = response.content.decode("utf-8")
        assert "/pillar-point/" in html
        assert "/duxbury/" in html
    else:
        # Should get a page prompting them to join a team
        assert response.status_code == 200
        assert "enter the code" in response.content.decode("utf-8")


def test_program_homepage_shows_assigned_shifts(
    admin_client, admin_user_has_shift, admin_user_has_past_shift
):
    response = admin_client.get("/programs/pillar-point/")
    assert len(response.context["upcoming_shifts"]) == 1


def test_code_to_join_program(admin_client):
    # Try with bad code
    response = admin_client.post("/join-program/", {"code": "bad-code"})
    assert response.status_code == 200
    assert "Invalid code" in response.content.decode("utf-8")
    team = Team.objects.get(slug="pillar-point")
    assert team.members.count() == 0
    code = TeamInviteCode.objects.create(team=team)
    response = admin_client.post("/join-program/", {"code": code.code})
    assert response.status_code == 302
    assert response.url == "/programs/pillar-point/"
    assert team.members.count() == 1


def test_render_calendar(admin_client, admin_user, admin_user_in_team, rf):
    # Test for just one month
    assert Shift.objects.count() == 0
    team = admin_user_in_team
    # Two other volunteers
    user1 = User.objects.create(username="one")
    user2 = User.objects.create(username="two")
    # Three shifts this month
    empty_shift = team.shifts.create(
        dawn=make_datetime(2022, 4, 3, 6),
        dusk=make_datetime(2022, 4, 3, 20),
        shift_start=make_datetime(2022, 4, 3, 8, 30),
        shift_end=make_datetime(2022, 4, 3, 8, 30),
    )
    # Current user is on this one
    user_is_on_shift = team.shifts.create(
        dawn=make_datetime(2022, 4, 7, 6),
        dusk=make_datetime(2022, 4, 7, 20),
        shift_start=make_datetime(2022, 4, 7, 8, 30),
        shift_end=make_datetime(2022, 4, 7, 8, 30),
    )
    user_is_on_shift.stewards.add(admin_user)
    # This one is full:
    full_shift = team.shifts.create(
        dawn=make_datetime(2022, 4, 21, 6),
        dusk=make_datetime(2022, 4, 21, 20),
        shift_start=make_datetime(2022, 4, 21, 8, 30),
        shift_end=make_datetime(2022, 4, 21, 8, 30),
    )
    full_shift.stewards.add(user1)
    full_shift.stewards.add(user2)
    request = rf.get("/")
    request.user = admin_user
    rendered = render_calendar(request, admin_user_in_team, 2022, 4)
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


class _Wildcard:
    def __eq__(self, other):
        return True


wildcard = _Wildcard()


def test_backup(admin_user_has_shift, client, settings):
    settings.BACKUP_SECRET = "backup-secret"
    # Test that it 400 errors without that secret
    assert client.get("/backup.json").status_code == 400
    assert (
        client.get("/backup.json", HTTP_AUTHORIZATION="Bearer bad-secret").status_code
        == 400
    )
    # With the correct secret it should work
    response = client.get("/backup.json", HTTP_AUTHORIZATION="Bearer backup-secret")
    assert response.status_code == 200
    assert response.json() == {
        "auth0_users": [],
        "users": [
            {
                "id": wildcard,
                "last_login": None,
                "username": "admin",
                "first_name": "",
                "last_name": "",
                "email": "admin@example.com",
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
                "date_joined": wildcard,
            }
        ],
        "shifts": [
            {
                "id": wildcard,
                "dawn": wildcard,
                "dusk": wildcard,
                "shift_start": wildcard,
                "shift_end": wildcard,
                "mllw_feet": None,
                "lowest_tide": None,
                "target_stewards": None,
                "steward_usernames": ["admin"],
            }
        ],
        "fragments": [
            {"slug": "contact_details", "fragment": "Contact details go here"}
        ],
    }
