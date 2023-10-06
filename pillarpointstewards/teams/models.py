from django.db import models
import random


class Team(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=32, unique=True)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(
        "auth.User", through="Membership", related_name="teams"
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "/programs/{}/".format(self.slug)


def generate_code():
    # Avoid easily confused letters and vowels to avoid accidental swear words
    return "".join(random.choice("BCDFGHJKMNPQRSTVWXYZ") for i in range(6))


class TeamInviteCode(models.Model):
    "A code that can be used to join a team"
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="codes")
    code = models.CharField(max_length=6, unique=True, default=generate_code)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "{} for {}".format(self.code, self.team)


class Membership(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="memberships"
    )
    is_admin = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} in {}".format(self.user, self.team)
