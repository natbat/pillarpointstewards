from django.db import models


class Shift(models.Model):
    dawn = models.DateTimeField()
    sunrise = models.DateTimeField(blank=True, null=True)
    sunset = models.DateTimeField(blank=True, null=True)
    dusk = models.DateTimeField()

    shift_start = models.DateTimeField()
    shift_end = models.DateTimeField()

    mllw_feet = models.IntegerField(blank=True, null=True)
    lowest_tide = models.DateTimeField(blank=True, null=True)

    stewards = models.ManyToManyField("auth.User", related_name="shifts")

    def __str__(self):
        return "{}-{}".format(self.shift_start, self.shift_end)
