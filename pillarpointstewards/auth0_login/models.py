from django.db import models
import secrets


def random_token():
    return secrets.token_hex(16)


class Auth0User(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    sub = models.CharField(unique=True, max_length=64)
    user = models.ForeignKey(
        "auth.User",
        related_name="auth0_users",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    details = models.JSONField(blank=True, null=True)

    def __str__(self):
        return "Auth0 sub '{}' is user '{}'".format(self.sub, self.user)
