from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import UserProfile
from shifts.models import Shift, Photo
from teams.models import Team
from django.utils import timezone


@login_required
def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    shared_team = (
        Team.objects.filter(members=request.user).filter(members=user).exists()
    )
    if not shared_team:
        return HttpResponseForbidden("You are not allowed to view that profile")

    profile = UserProfile.for_user(user)

    can_edit = request.user == user

    if request.method == "POST":
        profile.display_name = request.POST.get("display_name", "")
        profile.bio = request.POST.get("bio", "")
        profile.save()
        return redirect("user_profile", username=request.user.username)

    now = timezone.now()
    past_shifts = Shift.objects.filter(stewards=user, shift_end__lt=now).order_by(
        "-shift_start"
    )
    future_shifts = Shift.objects.filter(stewards=user, shift_start__gt=now).order_by(
        "shift_start"
    )

    context = {
        "profile_user": user,
        "profile": profile,
        "past_shifts": past_shifts,
        "future_shifts": future_shifts,
        "can_edit": can_edit,
    }
    return render(request, "profile.html", context)


@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile.display_name = request.POST.get("display_name", "")
        profile.bio = request.POST.get("bio", "")

        if "profile_photo" in request.FILES:
            photo = Photo.objects.create(
                owner=request.user, path=request.FILES["profile_photo"].name
            )
            profile.profile_photo = photo

        profile.save()
        return redirect("user_profile", username=request.user.username)

    context = {"profile": profile}
    return render(request, "profiles/edit_profile.html", context)
