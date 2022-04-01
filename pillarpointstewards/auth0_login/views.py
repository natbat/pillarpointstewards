from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from urllib.parse import urlencode
from .models import Auth0User
import os
import secrets
import httpx

AUTH0_DOMAIN = "pillarpointstewards.us.auth0.com"
AUTH0_CLIENT_ID = "DLXBMPbtamC2STUyV7R6OFJFDsSTHqEA"
AUTH0_CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET")


def login(request):
    redirect_uri = request.build_absolute_uri("/auth0-callback/")
    state = secrets.token_hex(16)
    url = "https://{}/authorize?".format(AUTH0_DOMAIN) + urlencode(
        {
            "response_type": "code",
            "client_id": AUTH0_CLIENT_ID,
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
        "https://{}/oauth/token".format(AUTH0_DOMAIN),
        data={
            "grant_type": "authorization_code",
            "redirect_uri": request.build_absolute_uri("/auth0-callback/"),
            "code": code,
        },
        auth=(AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET),
    )
    if response.status_code != 200:
        return HttpResponse(
            "Could not obtain access token: {}".format(response.status_code), status=500
        )

    # This should have returned an access token
    access_token = response.json()["access_token"]
    # Exchange that for the user info
    profile_response = httpx.get(
        "https://{}/userinfo".format(AUTH0_DOMAIN),
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
    user_to_sign_in = None
    if created:
        # If they have a verified email address create a Django user for them, or link to existing one
        if (
            profile.get("email_verified")
            and User.objects.filter(email=profile["email"]).count() == 1
        ):
            django_user = User.objects.get(email=profile["email"])
            auth0_user.user = django_user
            auth0_user.save()
            user_to_sign_in = django_user
        else:
            # Create a new Djngo user for them
            user_to_sign_in = User.objects.create(
                username=profile["nickname"],
                first_name=profile.get("given_name") or "",
                last_name=profile.get("family_name") or "",
                email=profile["email"],
                is_active=True,
            )
    else:
        # Is there a Django user we can sign them in as?
        if auth0_user.user:
            user_to_sign_in = auth0_user.user

    if user_to_sign_in:
        django_login(request, user_to_sign_in)
        return HttpResponseRedirect("/")
    else:
        return HttpResponse(
            "Your account has not yet been activated. Please contact Natalie Downe."
        )


def logout(request):
    django_logout(request)
    return HttpResponseRedirect("/")
