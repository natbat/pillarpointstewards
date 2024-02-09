from django.db import models
import secrets


def random_token():
    return secrets.token_hex(16)


class Shift(models.Model):
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="shifts",
    )

    dawn = models.DateTimeField(null=True, blank=True)
    dusk = models.DateTimeField(null=True, blank=True)

    shift_start = models.DateTimeField()
    shift_end = models.DateTimeField()

    mllw_feet = models.FloatField(blank=True, null=True)
    lowest_tide = models.DateTimeField(blank=True, null=True)
    target_stewards = models.IntegerField(blank=True, null=True)

    stewards = models.ManyToManyField("auth.User", related_name="shifts", blank=True)
    description = models.CharField(max_length=255, blank=True, default="")

    def can_edit(self, user):
        return self.team.is_admin(user)

    def get_absolute_url(self):
        return "/programs/{}/shifts/{}/".format(self.team.slug, self.id)

    @property
    def fullness(self):
        count = self.stewards.count()
        if count == 0:
            return "empty"
        if self.target_stewards and count >= self.target_stewards:
            return "full"
        else:
            return "partfull"

    def __str__(self):
        return "{}-{}".format(self.shift_start, self.shift_end)


class ShiftChange(models.Model):
    user = models.ForeignKey(
        "auth.User", related_name="shift_changes", on_delete=models.CASCADE
    )
    shift = models.ForeignKey(
        Shift, related_name="shift_changes", on_delete=models.CASCADE
    )
    change = models.CharField(max_length=32)
    when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} did {} to {} on {}".format(
            self.user, self.change, self.shift, self.when
        )


class SecretCalendar(models.Model):
    user = models.OneToOneField(
        "auth.User", related_name="secret_calendar", on_delete=models.CASCADE
    )
    secret = models.CharField(max_length=32, default=random_token)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Secret calendar URL for {}".format(self.user)

    @property
    def path(self):
        return "/shifts-personal-{}-{}.ics".format(self.pk, self.secret)

    @property
    def path_all(self):
        return "/shifts-all-{}-{}.ics".format(self.pk, self.secret)

    @property
    def calendar_url(self):
        if self.pk:
            return "https://www.pillarpointstewards.com{}".format(self.path)
        else:
            return ""

    @property
    def calendar_url_all(self):
        if self.pk:
            return "https://www.pillarpointstewards.com{}".format(self.path_all)
        else:
            return ""


class ShiftReport(models.Model):
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        related_name="shift_reports",
        null=True,
    )
    shift = models.ForeignKey(
        Shift, on_delete=models.CASCADE, related_name="shift_reports"
    )
    created = models.DateTimeField(auto_now_add=True)
    report = models.TextField()

    def get_absolute_url(self):
        return self.shift.get_absolute_url() + "#report-" + str(self.id)

    def __str__(self):
        user_str = self.user.username if self.user else "Deleted User"
        return f"Report by {user_str} on {self.shift}"


class ShiftReportQuestion(models.Model):
    team = models.ForeignKey(
        "teams.Team", on_delete=models.CASCADE, related_name="report_questions"
    )
    question = models.CharField(max_length=255)
    required = models.BooleanField(default=False)
    question_type = models.CharField(
        max_length=10,
        choices=[
            ("integer", "Integer"),
            ("float", "Float"),
            ("text", "Text"),
        ],
        default="text",
    )

    def __str__(self):
        return self.question


class ShiftReportAnswer(models.Model):
    report = models.ForeignKey(
        ShiftReport, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        ShiftReportQuestion, on_delete=models.CASCADE, related_name="answers"
    )
    answer_integer = models.IntegerField(blank=True, null=True)
    answer_float = models.FloatField(blank=True, null=True)
    answer_text = models.TextField(blank=True, null=True)

    def answer(self):
        if self.question.question_type == "integer":
            return str(self.answer_integer)
        elif self.question.question_type == "float":
            return str(self.answer_float)
        else:
            return self.answer_text

    def __str__(self):
        return f"Answer for {self.question} in {self.report}"
