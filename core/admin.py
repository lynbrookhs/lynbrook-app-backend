from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from .models import *


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    class MembershipAdmin(admin.StackedInline, DynamicArrayMixin):
        model = Membership
        extra = 0

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "grad_year")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "grad_year", "password1", "password2")}),
    )
    list_display = ("email", "first_name", "last_name", "is_staff")
    list_filter = ("is_staff", "is_superuser", "grad_year")
    search_fields = ("email", "first_name", "last_name")
    ordering = None
    inlines = (MembershipAdmin,)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    date_hierarchy = "start"
    list_display = ("name", "organization", "start", "end", "points", "user_count")
    list_filter = ("organization",)
    search_fields = ("name",)

    def user_count(self, obj):
        return obj.users.count()


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "day", "time", "link")
    list_filter = ("type", "day")


# @admin.register(Poll)
# class PollAdmin(admin.ModelAdmin, DynamicArrayMixin):
#     list_display = ("description", "post")
#     list_filter = ("post__organization",)


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "customizable")
    list_editable = ("customizable",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    class InlinePollAdmin(admin.StackedInline, DynamicArrayMixin):
        model = Poll
        extra = 0

    date_hierarchy = "date"
    list_display = ("title", "date", "organization", "published")
    list_filter = ("organization", "published")
    list_editable = ("published",)
    inlines = (InlinePollAdmin,)


@admin.register(Prize)
class PrizeAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "organization", "points")
    list_filter = ("organization",)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class InlinePeriodAdmin(admin.StackedInline, DynamicArrayMixin):
        model = SchedulePeriod
        extra = 0

    list_display = ("start", "end")
    inlines = (InlinePeriodAdmin,)
