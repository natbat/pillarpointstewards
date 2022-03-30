from django.contrib import admin
from .models import Shift


class ShiftAdmin(admin.ModelAdmin):
    model = Shift
    list_display = ("shift_start", "shift_end", "dawn", "dusk", "assigned")
    ordering = ("shift_start",)

    def assigned(self, obj):
        return ", ".join(obj.stewards.values_list("username", flat=True))


admin.site.register(Shift, ShiftAdmin)
