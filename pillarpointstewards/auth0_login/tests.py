import base64
from django.contrib.auth.models import User
from django.contrib.auth import get_user
from .models import Auth0User
from .utils import suggest_username
import pytest
import urllib.parse


def test_auth0_login(client, settings):
    response = client.get("/login/")
    assert response.status_code == 302
    location = response.headers["location"]
    bits = urllib.parse.urlparse(location)
    assert bits.netloc == settings.AUTH0_DOMAIN
    assert bits.path == "/authorize"
    qs = dict(urllib.parse.parse_qsl(bits.query))
    assert (
        qs.items()
        >= {
            "response_type": "code",
            "client_id": settings.AUTH0_CLIENT_ID,
            "redirect_uri": "http://testserver/auth0-callback/",
            "scope": "openid profile email",
        }.items()
    )
    # state should be a random string
    assert len(qs["state"]) == 32


@pytest.mark.parametrize(
    "auth0_profile,expected_user_properties",
    (
        (
            {
                "sub": "user1",
                "nickname": "simon",
                "email": "test@example.com",
            },
            {
                "is_superuser": False,
                "username": "simon",
                "first_name": "",
                "last_name": "",
                "email": "test@example.com",
                "is_staff": False,
                "is_active": True,
            },
        ),
        (
            {
                "sub": "user2",
                "nickname": "simon+otherstuff",
                "email": "simon+otherstuff@example.com",
            },
            {
                "is_superuser": False,
                "username": "simon-otherstuff",
                "first_name": "",
                "last_name": "",
                "email": "simon+otherstuff@example.com",
                "is_staff": False,
                "is_active": True,
            },
        ),
        (
            {
                "sub": "duplicate-nickname",
                "nickname": "existing-user",
                "email": "simon+existing@example.com",
            },
            {
                "is_superuser": False,
                "username": "existing-user-2",
                "first_name": "",
                "last_name": "",
                "email": "simon+existing@example.com",
                "is_staff": False,
                "is_active": True,
            },
        ),
    ),
)
def test_login_creates_account(
    db, httpx_mock, client, settings, auth0_profile, expected_user_properties
):
    _mock_oauth0(httpx_mock, settings, auth0_profile)
    # Create an existing user to test username conflict avoidance
    existing_user = User.objects.create(username="existing-user")
    Auth0User.objects.create(sub="existing", user=existing_user)

    assert "auth0-state" not in client.cookies
    client.get("/login/")
    assert "auth0-state" in client.cookies
    state = client.cookies["auth0-state"].value

    # Should start with one user
    assert User.objects.count() == 1
    assert Auth0User.objects.count() == 1
    existing_user_ids = list(User.objects.values_list("id", flat=True))

    response = client.get(f"/auth0-callback/?state={state}&code=x")
    assert response.status_code == 302

    # Should have created another user
    assert User.objects.count() == 2
    assert Auth0User.objects.count() == 2

    django_user = User.objects.exclude(id__in=existing_user_ids).get()
    assert get_user(client) == django_user
    for key, value in expected_user_properties.items():
        assert getattr(django_user, key) == value

    # And the Auth0User should exist and be linked to that user
    auth0_user = django_user.auth0_users.get()
    assert auth0_user.details == auth0_profile
    assert auth0_user.sub == auth0_profile["sub"]
    assert auth0_user.user == django_user

    # Finally check that the right calls were made to Auth0
    post_request, get_request = httpx_mock.get_requests()
    # post should have had client ID / secret in Authorization
    username_password = f"{settings.AUTH0_CLIENT_ID}:{settings.AUTH0_CLIENT_SECRET}"
    assert post_request.headers["authorization"] == "Basic {}".format(
        base64.b64encode(username_password.encode("latin-1")).decode("utf-8")
    )
    # get should have used the access token
    assert get_request.headers["authorization"] == "Bearer ACCESS_TOKEN"


def test_subsequent_login_logs_user_in(admin_user, httpx_mock, client, settings):
    _mock_oauth0(
        httpx_mock,
        settings,
        {
            "sub": "user|123",
            "nickname": "simon",
            "email": "test@example.com",
        },
    )
    Auth0User.objects.create(sub="user|123", user=admin_user)

    assert not get_user(client).is_authenticated

    client.get("/login/")
    state = client.cookies["auth0-state"].value
    response = client.get(f"/auth0-callback/?state={state}&code=x")
    assert response.status_code == 302

    assert get_user(client).is_authenticated
    assert get_user(client) == admin_user


def _mock_oauth0(httpx_mock, settings, auth0_profile):
    httpx_mock.add_response(
        url=f"https://{settings.AUTH0_DOMAIN}/oauth/token",
        json={"access_token": "ACCESS_TOKEN"},
    )
    httpx_mock.add_response(
        url=f"https://{settings.AUTH0_DOMAIN}/userinfo", json=auth0_profile
    )


@pytest.mark.parametrize(
    "input,expected",
    (
        ("simon+otherstuff", "simon-otherstuff"),
        ("simon willison", "simon-willison"),
        ("simoné --willîsonø", "simone-willison"),
    ),
)
def test_suggest_username(input, expected):
    assert suggest_username(input) == expected
