from django.shortcuts import render


def index(request):
    upcoming_shifts = []
    if request.user.is_authenticated:
        upcoming_shifts = list(request.user.shifts.order_by("shift_start"))
    return render(
        request,
        "index.html",
        {
            # TODO: upcoming only, taking timezone into account
            "upcoming_shifts": upcoming_shifts,
        },
    )


def patterns(request):
    return render(request, "patterns.html")
