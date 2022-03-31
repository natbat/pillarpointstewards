import calendar
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import get_template
from .models import Shift
import json


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
