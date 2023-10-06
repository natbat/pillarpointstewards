from django.contrib import admin
from .models import Team, Membership, TeamInviteCode


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 3


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    inlines = [MembershipInline]
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(TeamInviteCode)
class TeamInviteCodeAdmin(admin.ModelAdmin):
    list_display = ("team", "code", "is_active")
    list_filter = ("team", "is_active")
    search_fields = ("team__name", "code")
