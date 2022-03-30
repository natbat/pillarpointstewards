from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
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
