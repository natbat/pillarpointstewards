from django.contrib import admin
from .models import Shift, ShiftChange, SecretCalendar


class ShiftAdmin(admin.ModelAdmin):
    model = Shift
    list_display = ("shift_start", "shift_end", "team", "dawn", "dusk", "assigned")
    ordering = ("shift_start",)
    list_filter = ("team",)

    def assigned(self, obj):
        return ", ".join(obj.stewards.values_list("username", flat=True))


class SecretCalendarAdmin(admin.ModelAdmin):
    list_display = ("user", "created")
    readonly_fields = ("secret", "calendar_url")
    raw_id_fields = ("user",)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("user",)
        return self.readonly_fields


admin.site.register(Shift, ShiftAdmin)
admin.site.register(ShiftChange)
admin.site.register(SecretCalendar, SecretCalendarAdmin)
