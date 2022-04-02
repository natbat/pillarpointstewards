import base64
from django.contrib.auth.models import User
from .models import Auth0User
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
    ),
)
def test_login_creates_account(
    db, httpx_mock, client, settings, auth0_profile, expected_user_properties
):
    httpx_mock.add_response(
        url=f"https://{settings.AUTH0_DOMAIN}/oauth/token",
        json={"access_token": "ACCESS_TOKEN"},
    )
    httpx_mock.add_response(
        url=f"https://{settings.AUTH0_DOMAIN}/userinfo", json=auth0_profile
    )
    assert "auth0-state" not in client.cookies
    client.get("/login/")
    assert "auth0-state" in client.cookies
    state = client.cookies["auth0-state"].value

    # Should not be any users
    assert User.objects.count() == 0
    assert Auth0User.objects.count() == 0

    response = client.get(f"/auth0-callback/?state={state}&code=x")
    assert response.status_code == 302

    # Should have created a user
    assert User.objects.count() == 1
    assert Auth0User.objects.count() == 1

    django_user = User.objects.get()
    for key, value in expected_user_properties.items():
        assert getattr(django_user, key) == value

    # And the Auth0User should exist and be linked to that user
    auth0_user = Auth0User.objects.get()
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
