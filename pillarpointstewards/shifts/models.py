from django.db import models


class Shift(models.Model):
    dawn = models.DateTimeField()
    dusk = models.DateTimeField()

    shift_start = models.DateTimeField()
    shift_end = models.DateTimeField()

    mllw_feet = models.IntegerField(blank=True, null=True)
    lowest_tide = models.DateTimeField(blank=True, null=True)

    stewards = models.ManyToManyField("auth.User", related_name="shifts", blank=True)

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
