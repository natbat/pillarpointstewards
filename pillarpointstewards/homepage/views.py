from django.shortcuts import render
from .models import Fragment


def index(request):
    upcoming_shifts = []
    contact_details = ""
    if request.user.is_authenticated:
        upcoming_shifts = list(request.user.shifts.order_by("shift_start"))
        contact_details = Fragment.objects.get(slug="contact_details").fragment
    return render(
        request,
        "index.html",
        {
            # TODO: upcoming only, taking timezone into account
            "upcoming_shifts": upcoming_shifts,
            "contact_details": contact_details,
        },
    )


def patterns(request):
    return render(request, "patterns.html")
