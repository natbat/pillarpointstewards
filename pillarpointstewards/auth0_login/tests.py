import base64
from django.contrib.auth.models import User
from django.contrib.auth import get_user
from .models import Auth0User, ActiveUserSignupLink
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
            },
        ),
    ),
)
@pytest.mark.parametrize("use_secret_activation_link", (True, False))
def test_login_creates_account(
    db,
    httpx_mock,
    client,
    settings,
    auth0_profile,
    expected_user_properties,
    use_secret_activation_link,
):
    _mock_oauth0(httpx_mock, settings, auth0_profile)
    # Create an existing user to test username conflict avoidance
    existing_user = User.objects.create(username="existing-user")
    Auth0User.objects.create(sub="existing", user=existing_user)

    link = None
    if use_secret_activation_link:
        link = ActiveUserSignupLink.objects.create()
        client.get(link.path)
        assert "active-user-signup-link" in client.cookies

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

    # User should be active if they used a signup link, inactive otherwise
    assert django_user.is_active == use_secret_activation_link

    if use_secret_activation_link:
        assert link.created_users.filter(pk=django_user.id).exists()

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


@pytest.mark.parametrize(
    "path",
    (
        "/shifts/",
        "/shifts/SHIFT_ID/",
    ),
)
def test_pages_require_active_user(path, client, admin_user, admin_user_has_shift):
    path = path.replace("SHIFT_ID", str(admin_user.shifts.all()[0].pk))
    inactive_user = User.objects.create(username="inactive", is_active=False)
    logged_out_response = client.get(path)
    assert logged_out_response.status_code == 400
    client.force_login(inactive_user)
    inactive_response = client.get(path)
    assert inactive_response.status_code == 400
    client.force_login(admin_user)
    active_response = client.get(path)
    assert active_response.status_code == 200


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
