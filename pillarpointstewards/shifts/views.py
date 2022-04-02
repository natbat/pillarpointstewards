from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from .models import Shift, ShiftChange
from .ics_utils import calendar
from homepage.models import Fragment
from homepage.views import render_calendar
import json
import pytz


@login_required
def shift(request, shift_id):
    return render(
        request,
        "shift.html",
        {
            "shift": get_object_or_404(Shift, pk=shift_id),
            "contact_details": Fragment.objects.get(slug="contact_details").fragment,
        },
    )


@staff_member_required
def import_shifts(request):
    data = request.POST.get("data")
    if data:
        shifts = json.loads(data)
        for shift in shifts:
            Shift.objects.get_or_create(
                shift_start=shift["start"],
                shift_end=shift["end"],
                defaults={
                    "dawn": shift["dawn"],
                    "dusk": shift["dusk"],
                    "mllw_feet": shift["minTideFeet"],
                    "lowest_tide": shift["minTideTime"],
                    "target_stewards": shift["people"],
                },
            )
        return HttpResponseRedirect("/admin/shifts/shift/")

    return render(request, "import_shifts.html")


@login_required
def cancel_shift(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)
    if shift.stewards.filter(id=request.user.id).exists():
        shift.stewards.remove(request.user)
        shift.shift_changes.create(user=request.user, change="cancelled")
        return HttpResponse("Cancelled")
    else:
        return HttpResponse("You were not on that shift")


@login_required
def assign_shift(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)
    if not shift.stewards.filter(id=request.user.id).exists():
        shift.stewards.add(request.user)
        shift.shift_changes.create(user=request.user, change="assigned")
        return HttpResponse(
            render_calendar(request, shift.shift_start.year, shift.shift_start.month)
        )
    else:
        return HttpResponse("You were already on that shift")


@staff_member_required
def timeline(request):
    return render(
        request,
        "timeline.html",
        {
            "shift_changes": ShiftChange.objects.select_related(
                "shift", "user"
            ).order_by("-when")[:200],
        },
    )


def shifts(request):
    return render(request, "shifts.html", {
        "shifts": Shift.objects.prefetch_related("stewards"),
    })


def shifts_ics(request):
    def description(shift):
        stewards = ", ".join(shift.stewards.values_list("username", flat=True))
        stewards = "Stewards: {}".format(stewards) if stewards else "No stewards signed up yet"
        lines = [f"Shift from {shift.shift_start.time()} to {shift.shift_end.time()}", stewards]
        if shift.mllw_feet:
            lines.append(f"Low tide {shift.mllw_feet}ft at {shift.lowest_tide}")
        lines.append(f"https://www.pillarpointstewards.com/shifts/{shift.id}/")
        return "\n\n".join(lines)

    shifts = [
        {
            "name": "Steward shift at Pillar Point",
            "dtstart": shift.shift_start.isoformat().rstrip("Z"),
            "dtend": shift.shift_end.isoformat().rstrip("Z"),
            "description": description(shift),
            "tzid": "America/Los_Angeles",
            "id": str(shift.id),
        }
        for shift in Shift.objects.prefetch_related("stewards")
    ]
    s = calendar(shifts, title="Pillar Point Stewards")
    content_type = "text/calendar; charset=utf-8"
    if request.GET.get("_plain"):
        content_type = "text/plain; charset=utf-8"

    return HttpResponse(s, content_type=content_type)
