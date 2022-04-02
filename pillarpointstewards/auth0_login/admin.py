from django.contrib import admin
from .models import Auth0User, ActiveUserSignupLink

admin.site.register(Auth0User)
admin.site.register(ActiveUserSignupLink, readonly_fields=("signup_url",))
