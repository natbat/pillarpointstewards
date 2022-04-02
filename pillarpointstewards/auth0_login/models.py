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


class ActiveUserSignupLink(models.Model):
    secret = models.CharField(max_length=32, default=random_token)
    is_active = models.BooleanField(
        default=True,
        help_text="If not active the link will no longer create activated accounts",
    )
    created_users = models.ManyToManyField("auth.User", related_name="+", blank=True)
    comment = models.TextField(
        blank=True, null=True, help_text="Private note about where this URL was shared"
    )

    @property
    def users_created_with_this_link(self):
        # Avoid recursion error on /admin/auth0_login/activeusersignuplink/add/
        if self.pk:
            return ", ".join(self.created_users.values_list("username", flat=True))
        else:
            return ""

    @property
    def path(self):
        return "/signup/{}-{}/".format(self.pk, self.secret)

    @property
    def signup_url(self):
        if self.pk:
            return "https://www.pillarpointstewards.com{}".format(self.path)
        else:
            return ""

    def __str__(self):
        return f'Secret {self.secret} is {"active" if self.is_active else "inactive"} and has created {self.created_users.count()} users'
