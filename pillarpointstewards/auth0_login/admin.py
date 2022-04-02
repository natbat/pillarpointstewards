from django.contrib import admin
from .models import Auth0User, ActiveUserSignupLink

admin.site.register(Auth0User)
admin.site.register(
    ActiveUserSignupLink,
    readonly_fields=("secret", "signup_url", "users_created_with_this_link"),
    exclude=("created_users",),
    list_display=("secret", "is_active", "comment", "users_created_with_this_link"),
)
