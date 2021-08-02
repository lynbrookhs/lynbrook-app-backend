from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Event, Organization, Poll, Post, Prize, User


admin.site.register(User, UserAdmin)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "day", "time", "link")
    list_filter = ("type", "day")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    date_hierarchy = "date"
    list_display = ("title", "date", "organization", "published")
    list_filter = ("organization", "published")
    list_editable = ("published",)


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ("description", "post")
    list_filter = ("post__organization",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    date_hierarchy = "start"
    list_display = ("name", "organization", "start", "end", "points", "user_count")
    list_filter = ("organization",)
    search_fields = ("name",)

    def user_count(self, obj):
        return obj.users.count()


@admin.register(Prize)
class PrizeAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "organization", "points")
    list_filter = ("organization",)
