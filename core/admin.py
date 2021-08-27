import qrcode
from datauri import DataURI
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.shortcuts import render
from django.urls import path
from django.urls.base import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from qrcode.image.svg import SvgPathFillImage

from .models import *


def with_inline_organization_permissions(get_organization=lambda x: x):
    def deco(cls):
        class Admin(cls):
            def has_view_permission(self, request, obj=None):
                if obj is None or request.user.is_superuser:
                    return True
                org = get_organization(obj)
                return org.is_admin(request.user) or org.is_advisor(request.user)

            def has_change_permission(self, request, obj=None):
                return self.has_view_permission(request, obj)

            def has_add_permission(self, request, obj=None):
                return self.has_change_permission(request, obj)

            def has_delete_permission(self, request, obj=None):
                return self.has_change_permission(request, obj)

        return Admin

    return deco


def with_organization_permissions(get_organization=lambda x: x.organization, organization_field="organization"):
    def deco(cls):
        class Admin(cls):
            list_filter = (AdminAdvisorListFilter,)

            def has_module_permission(self, request):
                return True

            def has_view_permission(self, request, obj=None):
                if obj is None or request.user.is_superuser:
                    return True
                org = get_organization(obj)
                return org.is_admin(request.user) or org.is_advisor(request.user)

            def has_change_permission(self, request, obj=None):
                return self.has_view_permission(request, obj)

            def has_add_permission(self, request):
                return True

            def has_delete_permission(self, request, obj=None):
                return self.has_change_permission(request, obj)

            def get_queryset(self, request):
                qs = super().get_queryset(request)
                if request.user.is_superuser:
                    return qs
                return qs.filter(
                    Q(**{f"{organization_field}__admins": request.user})
                    | Q(**{f"{organization_field}__advisors": request.user})
                ).distinct()

            def get_form(self, request, obj=None, change=False, **kwargs):
                if not request.user.is_superuser:
                    form_class = cls.AdminAdvisorForm

                    class UserForm(form_class):
                        def __init__(self, *args, **kwargs):
                            super().__init__(*args, **kwargs)
                            q = Q(admins=request.user) | Q(advisors=request.user)
                            self.fields["organization"].queryset = (
                                self.fields["organization"].queryset.filter(q).distinct()
                            )

                    kwargs["form"] = UserForm

                return super().get_form(request, obj=obj, **kwargs)

        return Admin

    return deco


class AdminAdvisorListFilter(admin.SimpleListFilter):
    title = _("organization")

    parameter_name = "organization"

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            orgs = Organization.objects.all()
        else:
            orgs = Organization.objects.filter(Q(admins=request.user) | Q(advisors=request.user)).distinct()
        return [(org.id, org.name) for org in orgs]

    def queryset(self, request, queryset):
        if not self.value():
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

    class ExpoPushTokenAdmin(admin.TabularInline, DynamicArrayMixin):
        model = ExpoPushToken
        extra = 0

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "type", "grad_year")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "grad_year", "password1", "password2")}),)
    list_display = ("email", "first_name", "last_name", "is_staff")
    list_filter = ("is_staff", "is_superuser", "grad_year")
    search_fields = ("email", "first_name", "last_name")
    ordering = None
    inlines = (AdvisorOrganizationAdmin, AdminOrganizationAdmin, MembershipAdmin, ExpoPushTokenAdmin)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin, DynamicArrayMixin):
    @with_inline_organization_permissions()
    class InlineLinkAdmin(admin.TabularInline, DynamicArrayMixin):
        model = OrganizationLink
        extra = 0

        def has_view_permission(self, request, obj=None):
            print(obj)
            return super().has_view_permission(request, obj=obj)

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

    list_display = ("name", "type", "day", "time", "link", "points_link")
    list_filter = ("type", "day", "category")
    readonly_fields = ("points_link",)
    autocomplete_fields = ("advisors", "admins")
    inlines = (InlineLinkAdmin,)

    def has_module_permission(self, request):
        return True

    def has_view_permission(self, request, obj=None):
        if obj is None or request.user.is_superuser:
            return True
        return obj.is_admin(request.user) or obj.is_advisor(request.user)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(Q(admins=request.user) | Q(advisors=request.user)).distinct()

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser:
            kwargs["form"] = self.AdvisorForm if obj.is_advisor(request.user) else self.AdminForm
        return super().get_form(request, obj=obj, **kwargs)

    def points_link(self, obj):
        return mark_safe(f'<a href={reverse("admin:core_organization_points", args=[obj.id])}>View Points</a>')

    def get_urls(self):
        return [
            path("<path:object_id>/points/", self.points_view, name="core_organization_points"),
            *super().get_urls(),
        ]

    def points_view(self, request, object_id):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related(
            Prefetch("memberships", Membership.objects.select_related("user").order_by("-points")),
            Prefetch("events", Event.objects.prefetch_related("submissions")),
        )
        try:
            org = qs.get(id=object_id)
        except self.model.DoesNotExist:
            return self._get_obj_does_not_exist_redirect(request, self.model._meta, object_id)

        events = [(e, set(x.user_id for x in e.submissions.all())) for e in org.events.all()]

        context = dict(
            org=org,
            events=[event.name for event, _ in events],
            members=[
                dict(
                    **membership.user.to_json(),
                    points=membership.points,
                    events=[event.points if membership.user.id in users else None for event, users in events],
                )
                for membership in org.memberships.all()
            ],
        )
        return render(request, "core/organization_points.html", context)


@admin.register(Event)
@with_organization_permissions()
class EventAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class AdminAdvisorForm(forms.ModelForm):
        class Meta:
            fields = ("organization", "name", "description", "start", "end", "points", "submission_type")

    date_hierarchy = "start"
    list_display = ("name", "organization", "start", "end", "points", "user_count")
    search_fields = ("name",)
    readonly_fields = ("code", "qr_code")

    def user_count(self, obj):
        return obj.users.count()

    @admin.display(description="QR Code")
    def qr_code(self, obj):
        if obj.code is None:
            return "-"
        qr_svg = qrcode.make(f"lhs://{obj.code}", image_factory=SvgPathFillImage, box_size=50, border=0)
        uri_svg = DataURI.make("image/svg+xml", charset="UTF-8", base64=True, data=qr_svg.to_string())
        return mark_safe(f'<img src="{uri_svg}" alt="lhs://{obj.code}">')


@admin.register(Submission)
@with_organization_permissions(lambda x: x.event.organization, "event__organization")
class SubmissionAdmin(admin.ModelAdmin, DynamicArrayMixin):
    model = Submission
    search_fields = ("event__name", "user__first_name", "user__last_name")
    list_display = ("user", "event", "file")


@admin.register(Post)
@with_organization_permissions()
class PostAdmin(admin.ModelAdmin, DynamicArrayMixin):
    @with_inline_organization_permissions(lambda x: x.organization)
    class InlinePollAdmin(admin.StackedInline, DynamicArrayMixin):
        model = Poll
        extra = 0

    class AdminAdvisorForm(forms.ModelForm):
        class Meta:
            fields = ("organization", "title", "content", "published")

    date_hierarchy = "date"
    list_display = ("title", "date", "organization", "published")
    list_filter = ("organization", "published")
    list_editable = ("published",)
    inlines = (InlinePollAdmin,)


@admin.register(Prize)
@with_organization_permissions()
class PrizeAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class AdminAdvisorForm(forms.ModelForm):
        class Meta:
            fields = ("organization", "name", "description", "points")

    list_display = ("name", "description", "organization", "points")
    list_filter = ("organization",)


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin, DynamicArrayMixin):
    list_display = ("id", "name", "customizable")
    list_editable = ("customizable",)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class InlinePeriodAdmin(admin.TabularInline, DynamicArrayMixin):
        model = SchedulePeriod
        extra = 0

    list_display = ("name", "start", "end", "weekday", "priority")
    inlines = (InlinePeriodAdmin,)
    save_as = True
