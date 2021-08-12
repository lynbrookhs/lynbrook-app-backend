import functools

import qrcode
from datauri import DataURI
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from qrcode.image.svg import SvgPathFillImage

from .models import *

admin.site.site_header = "Lynbrook ASB"


def with_organization_permissions(cls):
    class Admin(cls):
        list_filter = (AdminAdvisorListFilter,)

        def has_module_permission(self, request):
            return True

        def has_add_permission(self, request):
            return True

        def has_view_permission(self, request, obj=None):
            if obj is None:
                return True
            return obj.organization.is_admin(request.user) or obj.organization.is_advisor(request.user)

        def has_change_permission(self, request, obj=None):
            return self.has_view_permission(request, obj)

        def has_delete_permission(self, request, obj=None):
            return self.has_change_permission(request, obj)

        def get_queryset(self, request):
            qs = super().get_queryset(request)
            return qs.filter(Q(organization__admins=request.user) | Q(organization__advisors=request.user))

        def get_form(self, request, obj=None, change=False, **kwargs):
            if not request.user.is_superuser:
                form_class = cls.AdminAdvisorForm

                class UserForm(form_class):
                    def __init__(self, *args, **kwargs):
                        super().__init__(user=request.user, *args, **kwargs)

                kwargs["form"] = UserForm

            return super().get_form(request, obj=obj, **kwargs)

    return Admin


class AdminAdvisorListFilter(admin.SimpleListFilter):
    title = _("organization")

    parameter_name = "organization"

    def lookups(self, request, model_admin):
        orgs = Organization.objects.filter(Q(admins=request.user) | Q(advisors=request.user))
        return [(org.id, org.name) for org in orgs]

    def queryset(self, request, queryset):
        if not self.value() or request.user.is_superuser:
            return queryset
        return queryset.filter(organization=self.value())


@admin.register(User)
class UserAdmin(BaseUserAdmin, DynamicArrayMixin):
    class AdvisorOrganizationAdmin(admin.TabularInline, DynamicArrayMixin):
        model = Organization.advisors.through
        verbose_name = "Organization"
        verbose_name_plural = "Advisor For"
        extra = 0

    class AdminOrganizationAdmin(admin.TabularInline, DynamicArrayMixin):
        model = Organization.admins.through
        verbose_name = "Organization"
        verbose_name_plural = "Admin For"
        extra = 0

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
    inlines = (AdvisorOrganizationAdmin, AdminOrganizationAdmin)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class InlineLinkAdmin(admin.TabularInline, DynamicArrayMixin):
        model = OrganizationLink
        extra = 0

    class AdvisorForm(forms.ModelForm):
        class Meta:
            fields = (
                "advisors",
                "admins",
                "name",
                "description",
                "category",
                "day",
                "time",
                "link",
                "ical_links",
            )

    class AdminForm(forms.ModelForm):
        class Meta:
            fields = (
                "admins",
                "name",
                "description",
                "category",
                "day",
                "time",
                "link",
                "ical_links",
            )

    list_display = ("name", "type", "day", "time", "link")
    list_filter = ("type", "day", "category")
    autocomplete_fields = ("advisors", "admins")
    inlines = (InlineLinkAdmin,)

    def has_module_permission(self, request):
        return True

    def has_view_permission(self, request, obj=None):
        if obj is None:
            return True
        return obj.is_admin(request.user) or obj.is_advisor(request.user)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(Q(admins=request.user) | Q(advisors=request.user))

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            kwargs["form"] = self.AdvisorForm if obj.is_advisor(request.user) else self.AdminForm
        return super().get_form(request, obj=obj, **kwargs)


@admin.register(Event)
@with_organization_permissions
class EventAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class AdminAdvisorForm(forms.ModelForm):
        class Meta:
            fields = ("organization", "name", "description", "start", "end", "points", "submission_type")

        def __init__(self, user, *args, **kwargs):
            super().__init__(*args, **kwargs)
            q = Q(admins=user) | Q(advisors=user)
            self.fields["organization"].queryset = self.fields["organization"].queryset.filter(q)

    date_hierarchy = "start"
    list_display = ("name", "organization", "start", "end", "points", "user_count")
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


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin, DynamicArrayMixin):
    list_display = ("id", "name", "customizable")
    list_editable = ("customizable",)


@admin.register(Post)
@with_organization_permissions
class PostAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class InlinePollAdmin(admin.StackedInline, DynamicArrayMixin):
        model = Poll
        extra = 0

    class AdminAdvisorForm(forms.ModelForm):
        class Meta:
            fields = ("organization", "title", "content", "published")

        def __init__(self, user, *args, **kwargs):
            super().__init__(*args, **kwargs)
            q = Q(admins=user) | Q(advisors=user)
            self.fields["organization"].queryset = self.fields["organization"].queryset.filter(q)

    date_hierarchy = "date"
    list_display = ("title", "date", "organization", "published")
    list_filter = ("organization", "published")
    list_editable = ("published",)
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
    save_as = True
