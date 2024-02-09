from django.contrib import admin
from .models import (
    Shift,
    ShiftChange,
    ShiftReport,
    ShiftReportQuestion,
    ShiftReportAnswer,
    SecretCalendar,
)


class ShiftAdmin(admin.ModelAdmin):
    model = Shift
    list_display = (
        "shift_start",
        "shift_end",
        "team",
        "target_stewards",
        "assigned",
        "dawn",
        "dusk",
    )
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


class ShiftReportAdmin(admin.ModelAdmin):
    model = ShiftReport
    list_display = ("shift", "user", "created")
    ordering = ("-created",)
    raw_id_fields = ("shift", "user")


class ShiftReportQuestionAdmin(admin.ModelAdmin):
    model = ShiftReportQuestion
    list_display = ("team", "question", "required", "question_type")
    list_filter = ("team",)
    ordering = ("team",)


class ShiftReportAnswerAdmin(admin.ModelAdmin):
    model = ShiftReportAnswer
    list_display = ("report_team", "report", "question", "answer")
    list_filter = ("question",)
    ordering = ("report",)

    def report_team(self, obj):
        return obj.report.shift.team


admin.site.register(Shift, ShiftAdmin)
admin.site.register(ShiftChange)
admin.site.register(ShiftReport, ShiftReportAdmin)
admin.site.register(ShiftReportQuestion, ShiftReportQuestionAdmin)
admin.site.register(ShiftReportAnswer, ShiftReportAnswerAdmin)
admin.site.register(SecretCalendar, SecretCalendarAdmin)
