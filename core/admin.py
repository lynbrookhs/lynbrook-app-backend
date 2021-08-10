import qrcode
from datauri import DataURI
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from qrcode.image.svg import SvgPathFillImage

from .models import *

admin.site.site_header = "Lynbrook ASB"


@admin.register(User)
class UserAdmin(BaseUserAdmin, DynamicArrayMixin):
    class MembershipAdmin(admin.TabularInline, DynamicArrayMixin):
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
class EventAdmin(admin.ModelAdmin, DynamicArrayMixin):
    date_hierarchy = "start"
    list_display = ("name", "organization", "start", "end", "points", "user_count")
    list_filter = ("organization",)
    search_fields = ("name",)
    readonly_fields = ("code", "qr_code")
    autocomplete_fields = ("users",)

    def user_count(self, obj):
        return obj.users.count()

    @admin.display(description="QR Code")
    def qr_code(self, obj):
        qr_svg = qrcode.make(f"lhs://{obj.code}", image_factory=SvgPathFillImage, box_size=50, border=0)
        uri_svg = DataURI.make("image/svg+xml", charset="UTF-8", base64=True, data=qr_svg.to_string())
        return mark_safe(f'<img src="{uri_svg}" alt="lhs://{obj.code}">')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class InlineLinkAdmin(admin.TabularInline, DynamicArrayMixin):
        model = OrganizationLink
        extra = 0

    list_display = ("name", "type", "day", "time", "link")
    list_filter = ("type", "day", "category")
    inlines = (InlineLinkAdmin,)


# @admin.register(Poll)
# class PollAdmin(admin.ModelAdmin, DynamicArrayMixin):
#     list_display = ("description", "post")
#     list_filter = ("post__organization",)


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin, DynamicArrayMixin):
    list_display = ("id", "name", "customizable")
    list_editable = ("customizable",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class InlinePollAdmin(admin.StackedInline, DynamicArrayMixin):
        model = Poll
        extra = 0

    date_hierarchy = "date"
    list_display = ("title", "date", "organization", "published")
    list_filter = ("organization", "published")
    list_editable = ("published",)
    ordering = ("-date",)
    inlines = (InlinePollAdmin,)


@admin.register(Prize)
class PrizeAdmin(admin.ModelAdmin, DynamicArrayMixin):
    list_display = ("name", "description", "organization", "points")
    list_filter = ("organization",)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class InlinePeriodAdmin(admin.TabularInline, DynamicArrayMixin):
        model = SchedulePeriod
        extra = 0

    list_display = ("name", "start", "end", "weekday", "priority")
    inlines = (InlinePeriodAdmin,)
    ordering = ("-priority",)
    save_as = True
