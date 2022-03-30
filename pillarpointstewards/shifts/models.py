from django.db import models


class Shift(models.Model):
    dawn = models.DateTimeField()
    sunrise = models.DateTimeField()
    sunset = models.DateTimeField()
    dusk = models.DateTimeField()

    shift_start = models.DateTimeField()
    shift_end = models.DateTimeField()

    mllw_feet = models.IntegerField()
    lowest_tide = models.DateTimeField()

    stewards = models.ManyToManyField("auth.User", related_name="shifts")

    def __str__(self):
        return "{}-{}".format(self.shift_start, self.shift_end)
