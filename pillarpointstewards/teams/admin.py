from django.contrib import admin
from .models import Team, Membership


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 3


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    inlines = [MembershipInline]
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
