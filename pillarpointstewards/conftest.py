import datetime
import pytest
import pytz


@pytest.fixture(autouse=True)
def configure_whitenoise(settings):
    """
    Get rid of whitenoise "No directory at" warning, as it's not helpful when running tests.
    https://github.com/evansd/whitenoise/issues/215#issuecomment-558621213
    """
    settings.WHITENOISE_AUTOREFRESH = True


@pytest.fixture
def admin_user_in_team(admin_user):
    from teams.models import Team

    team = Team.objects.get_or_create(name="Pillar Point", slug="pillar-point")[0]
    team.memberships.get_or_create(user=admin_user, is_admin=True)
    return team


@pytest.fixture
def admin_user_has_shift(admin_user, admin_user_in_team):
    from teams.models import Team
    from tides.models import Location
    from django.contrib.auth.models import User

    dt = datetime.datetime.utcnow().replace(
        tzinfo=pytz.timezone("America/Los_Angeles")
    ) + datetime.timedelta(hours=96)
    # Create a shift in some other team as well
    other_team = Team.objects.get_or_create(
        name="Other Team",
        slug="other-team",
        location=Location.objects.get_or_create(
            name="Laguna Beach",
            station_id="9410580",
            latitude=33.5414769,
            longitude=-117.790039,
            time_zone="America/Los_Angeles",
        )[0],
    )[0]
    other_user = User.objects.get_or_create(username="other")[0]
    other_team.memberships.get_or_create(user=other_user)
    other_user.shifts.create(
        team=other_team,
        shift_start=dt,
        shift_end=dt + datetime.timedelta(hours=2),
        dawn=dt - datetime.timedelta(hours=1),
        dusk=dt + datetime.timedelta(hours=5),
    )
    return admin_user.shifts.create(
        team=admin_user_in_team,
        shift_start=dt,
        shift_end=dt + datetime.timedelta(hours=2),
        dawn=dt - datetime.timedelta(hours=1),
        dusk=dt + datetime.timedelta(hours=5),
    )


@pytest.fixture
def admin_user_has_past_shift(admin_user, admin_user_in_team):
    dt = datetime.datetime.utcnow().replace(
        tzinfo=pytz.timezone("America/Los_Angeles")
    ) - datetime.timedelta(hours=96)
    admin_user.shifts.create(
        shift_start=dt,
        shift_end=dt + datetime.timedelta(hours=2),
        team=admin_user_in_team,
        dawn=dt - datetime.timedelta(hours=1),
        dusk=dt + datetime.timedelta(hours=5),
    )


@pytest.fixture(autouse=True)
def use_dummy_auth0_client_secret(settings):
    settings.AUTH0_CLIENT_SECRET = "auth0-test-client-secret"
