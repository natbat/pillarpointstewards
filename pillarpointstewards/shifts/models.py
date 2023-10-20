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

    dawn = models.DateTimeField()
    dusk = models.DateTimeField()

    shift_start = models.DateTimeField()
    shift_end = models.DateTimeField()

    mllw_feet = models.FloatField(blank=True, null=True)
    lowest_tide = models.DateTimeField(blank=True, null=True)
    target_stewards = models.IntegerField(blank=True, null=True)

    stewards = models.ManyToManyField("auth.User", related_name="shifts", blank=True)

    def can_edit(self, user):
        return self.team.is_admin(user)

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
    def calendar_url(self):
        if self.pk:
            return "https://www.pillarpointstewards.com{}".format(self.path)
        else:
            return ""
