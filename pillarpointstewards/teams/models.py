from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=32, unique=True)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(
        "auth.User", through="Membership", related_name="teams"
    )

    def __str__(self):
        return self.name


class Membership(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="memberships"
    )
    is_admin = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} in {}".format(self.user, self.team)
