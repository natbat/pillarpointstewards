import base64

from django.conf import settings
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from django.core import signing
from django.http import HttpResponse, HttpResponseRedirect
from urllib.parse import urlencode

from django.shortcuts import get_object_or_404
from .models import Auth0User, ActiveUserSignupLink
from .utils import suggest_username
import secrets
import httpx


def signup(request):
    return login(request, signup=True)


def signed_base64(value, key):
    signed = signing.Signer(key=key).sign(value)
    return base64.urlsafe_b64encode(signed.encode()).decode()


def login(request, signup=False):
    redirect_uri = request.build_absolute_uri("/auth0-callback/")

    forward_url = getattr(settings, "AUTH0_FORWARD_URL", None)
    print("forward_url", forward_url)
    if forward_url:
        redirect_uri = (
            forward_url
            + "?forward="
            + signed_base64(redirect_uri, settings.AUTH0_FORWARD_SECRET)
        )
        print("redirect_uri", redirect_uri)

    state = secrets.token_hex(16)
    kwargs = {
        "response_type": "code",
        "client_id": settings.AUTH0_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "openid profile email",
        "state": state,
    }
    if signup:
        kwargs["screen_hint"] = "signup"

    url = "https://{}/authorize?".format(settings.AUTH0_DOMAIN) + urlencode(kwargs)
    response = HttpResponseRedirect(url)
    response.set_cookie("auth0-state", state, max_age=3600)
    return response


def secret_signup(request, id, key):
    link = get_object_or_404(ActiveUserSignupLink, pk=id)
    response = HttpResponseRedirect("/signup/")
    if secrets.compare_digest(link.secret, key):
        # Set a cookie to activate their account on completion
        response.set_signed_cookie("active-user-signup-link", str(link.id))
    return response


def callback(request):
    forward = request.GET.get("forward")
    if forward:
        # If signature check passes, redirect to this instead
        secret = settings.AUTH0_FORWARD_SECRET
        signer = signing.Signer(key=secret)
        try:
            redirect_uri = signer.unsign(
                base64.urlsafe_b64decode(forward.encode()).decode()
            )
            # Glue on query string arguments except for forward=
            new_qs = {
                key: value for key, value in request.GET.items() if key != "forward"
            }
            return HttpResponseRedirect(redirect_uri + "?" + urlencode(new_qs))
        except signing.BadSignature:
            return HttpResponse("Invalid signature", status=400)

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

    # User will be set to active IF they started at a secret link
    is_active = False
    link_to_credit = None
    signup_link_id = request.get_signed_cookie("active-user-signup-link", default=None)
    if signup_link_id:
        try:
            link = ActiveUserSignupLink.objects.get(pk=signup_link_id)
            if link.is_active:
                is_active = True
                link_to_credit = link
        except ActiveUserSignupLink.DoesNotExist:
            pass

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
                    is_active=is_active,
                )
                break
            except IntegrityError:
                if suffix is None:
                    suffix = 1
                # Always start at 2
                suffix += 1

    if link_to_credit:
        link_to_credit.created_users.add(django_user)

    auth0_user.user = django_user
    auth0_user.save()
    django_login(request, django_user)
    return HttpResponseRedirect("/")


def logout(request):
    django_logout(request)
    redirect_uri = request.build_absolute_uri("/")
    url = "https://{}/v2/logout?".format(settings.AUTH0_DOMAIN) + urlencode(
        {
            "client_id": settings.AUTH0_CLIENT_ID,
            "returnTo": redirect_uri,
        }
    )
    return HttpResponseRedirect(url)
