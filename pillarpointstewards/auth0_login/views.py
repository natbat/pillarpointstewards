from django.conf import settings
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from urllib.parse import urlencode
from .models import Auth0User
from .utils import suggest_username
import secrets
import httpx


def login(request):
    redirect_uri = request.build_absolute_uri("/auth0-callback/")
    state = secrets.token_hex(16)
    url = "https://{}/authorize?".format(settings.AUTH0_DOMAIN) + urlencode(
        {
            "response_type": "code",
            "client_id": settings.AUTH0_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": "openid profile email",
            "state": state,
        }
    )
    response = HttpResponseRedirect(url)
    response.set_cookie("auth0-state", state, max_age=3600)
    return response


def callback(request):
    code = request.GET.get("code") or ""
    state = request.GET.get("state") or ""
    # Compare state to their cookie
    expected_state = request.COOKIES.get("auth0-state") or ""
    if not state or not secrets.compare_digest(state, expected_state):
        return HttpResponse(
            "state check failed, your authentication request is no longer valid",
            status=500,
        )

    # Exchange the code for an access token
    response = httpx.post(
        "https://{}/oauth/token".format(settings.AUTH0_DOMAIN),
        data={
            "grant_type": "authorization_code",
            "redirect_uri": request.build_absolute_uri("/auth0-callback/"),
            "code": code,
        },
        auth=(settings.AUTH0_CLIENT_ID, settings.AUTH0_CLIENT_SECRET),
    )
    if response.status_code != 200:
        return HttpResponse(
            "Could not obtain access token: {}".format(response.status_code), status=500
        )

    # This should have returned an access token
    access_token = response.json()["access_token"]
    # Exchange that for the user info
    profile_response = httpx.get(
        "https://{}/userinfo".format(settings.AUTH0_DOMAIN),
        headers={"Authorization": "Bearer {}".format(access_token)},
    )
    if profile_response.status_code != 200:
        return HttpResponse(
            "Could not fetch profile: {}".format(response.status_code), status=500
        )

    profile = profile_response.json()

    auth0_user, created = Auth0User.objects.get_or_create(
        sub=profile["sub"], defaults={"details": profile}
    )

    if auth0_user.user:
        django_login(request, auth0_user.user)
        return HttpResponseRedirect("/")

    # Need to create a new Django user for that auth0_user, with a unique username
    # derived from their nickname but avoiding duplicates
    base_username = suggest_username(profile["nickname"])
    suffix = None
    while True:
        # Keep going until we don't get an IntegrityError
        username = base_username
        if suffix:
            username += f"-{suffix}"
        with transaction.atomic():
            try:
                django_user = User.objects.create(
                    username=username,
                    first_name=profile.get("given_name") or "",
                    last_name=profile.get("family_name") or "",
                    email=profile["email"],
                    is_active=False,
                )
                break
            except IntegrityError:
                if suffix is None:
                    suffix = 1
                # Always start at 2
                suffix += 1

    auth0_user.user = django_user
    auth0_user.save()
    django_login(request, django_user)
    return HttpResponseRedirect("/")


def logout(request):
    django_logout(request)
    return HttpResponseRedirect("/")
