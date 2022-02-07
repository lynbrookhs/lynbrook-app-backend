import csv
import io

import qrcode
from datauri import DataURI
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http.response import Http404, HttpResponse
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


def with_organization_permissions():
    def deco(cls):
        class Admin(cls):
            def has_module_permission(self, request):
                return True

            def has_view_permission(self, request, obj=None):
                if obj is None or request.user.is_superuser:
                    return True
                return obj.organization.is_admin(request.user) or obj.organization.is_advisor(request.user)

            def has_change_permission(self, request, obj=None):
                return self.has_view_permission(request, obj)

            def has_delete_permission(self, request, obj=None):
                return self.has_change_permission(request, obj)

            def get_queryset(self, request):
                qs = super().get_queryset(request)
                if request.user.is_superuser:
                    return qs
                return qs.filter(
                    Q(**{f"organization__admins": request.user}) | Q(**{f"organization__advisors": request.user})
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


class EventListFilter(admin.SimpleListFilter):
    title = _("event")

    parameter_name = "event"

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            events = Event.objects.all()
        else:
            events = Event.objects.filter(
                Q(organization__admins=request.user) | Q(organization__advisors=request.user)
            ).distinct()
        return [(event.id, event) for event in events]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        return queryset.filter(event=self.value())


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

    def has_view_permission(self, request, obj=None):
        return True


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

    list_display = ("name", "type", "day", "time", "location", "points_link")
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
            path("<path:object_id>/points/csv/", self.points_csv_view, name="core_organization_points"),
            path("<path:object_id>/points/", self.points_view, name="core_organization_points"),
            *super().get_urls(),
        ]

    def get_org_with_points(self, request, object_id):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related(
            Prefetch("memberships", Membership.objects.select_related("user").order_by("-points")),
            Prefetch("events", Event.objects.prefetch_related("submissions")),
        )
        return qs.get(id=object_id)

    def points_view(self, request, object_id):
        try:
            org = self.get_org_with_points(request, object_id)
        except self.model.DoesNotExist:
            return self._get_obj_does_not_exist_redirect(request, self.model._meta, object_id)

        events = [
            (e, {x.user_id: e.points if x.points is None else x.points for x in e.submissions.all()})
            for e in org.events.all()
        ]
        context = dict(
            org=org,
            events=[event.name for event, _ in events],
            members=[
                dict(
                    **membership.user.to_json(),
                    points=membership.points,
                    events=[users.get(membership.user.id) for event, users in events],
                )
                for membership in org.memberships.all()
            ],
        )

        return render(request, "core/organization_points.html", context)

    def points_csv_view(self, request, object_id):
        try:
            org = self.get_org_with_points(request, object_id)
        except self.model.DoesNotExist:
            raise Http404

        events = [
            (e, {x.user_id: e.points if x.points is None else x.points for x in e.submissions.all()})
            for e in org.events.all()
        ]
        response = HttpResponse(
            content_type="text/csv", headers={"Content-Disposition": 'attachment; filename="points.csv"'}
        )
        writer = csv.DictWriter(
            response,
            fieldnames=["id", "email", "first_name", "last_name", "grad_year", "points", *[e.name for e, _ in events]],
        )
        writer.writeheader()
        for membership in org.memberships.all():
            writer.writerow(
                dict(
                    **membership.user.to_json(),
                    points=membership.points,
                    **{event.name: users.get(membership.user.id) for event, users in events},
                )
            )
        return response


@admin.register(Event)
@with_organization_permissions()
class EventAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class AdminAdvisorForm(forms.ModelForm):
        class Meta:
            fields = ("organization", "name", "description", "start", "end", "points", "submission_type")

    list_filter = (AdminAdvisorListFilter,)
    date_hierarchy = "start"
    list_display = ("name", "organization", "start", "end", "points", "user_count")
    search_fields = ("name",)
    readonly_fields = ("code", "qr_code", "sign_in")

    def user_count(self, obj):
        return obj.users.count()

    @admin.display(description="QR Code")
    def qr_code(self, obj):
        if obj.code is None:
            return "-"
        qr_svg = qrcode.make(f"lhs://{obj.code}", image_factory=SvgPathFillImage, box_size=50, border=0)
        uri_svg = DataURI.make("image/svg+xml", charset="UTF-8", base64=True, data=qr_svg.to_string())
        return mark_safe(f'<img src="{uri_svg}" alt="lhs://{obj.code}">')

    @admin.display(description="Sign In Instructions")
    def sign_in(self, obj):
        return mark_safe(
            """
            <p>Members can sign in in one of the following ways:</p>
            <p>• Scanning the QR Code in the Lynbrook App</li></p>
            <p>• Entering the 6-digit code manually in the Lynbrook App</li></p>
            <p>• Entering the 6-digit code in the web form at <a href="https://lynbrookasb.org/">https://lynbrookasb.org/</a></li></p>
            """
        )

    def has_add_permission(self, request):
        return True


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class AdminAdvisorForm(forms.ModelForm):
        class Meta:
            fields = ("event", "user", "points")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        events = Event.objects.filter(
            Q(**{f"organization__admins": request.user}) | Q(**{f"organization__advisors": request.user})
        )
        return qs.filter(event__in=events)

    list_filter = (EventListFilter,)
    search_fields = ("event__name", "user__first_name", "user__last_name")
    list_display = ("user", "event", "points", "file")
    autocomplete_fields = ("user", "event")

    def organization(self, obj):
        return obj.event.organization

    def has_module_permission(self, request):
        return True

    def has_view_permission(self, request, obj=None):
        if obj is None or request.user.is_superuser:
            return True
        return obj.event.organization.is_admin(request.user) or obj.event.organization.is_advisor(request.user)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_add_permission(self, request):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(
            Q(**{f"event__organization__admins": request.user}) | Q(**{f"event__organization__advisors": request.user})
        ).distinct()

    def get_form(self, request, obj=None, change=False, **kwargs):
        if not request.user.is_superuser:
            form_class = self.AdminAdvisorForm

            class UserForm(form_class):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    q = Q(organization__admins=request.user) | Q(organization__advisors=request.user)
                    self.fields["event"].queryset = (
                        self.fields["event"].queryset.filter(q).order_by("-start").distinct()
                    )

            kwargs["form"] = UserForm

        return super().get_form(request, obj=obj, **kwargs)


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

    list_filter = (AdminAdvisorListFilter,)
    date_hierarchy = "date"
    list_display = ("title", "date", "organization", "published")
    list_filter = ("organization", "published")
    list_editable = ("published",)
    inlines = (InlinePollAdmin,)

    def has_add_permission(self, request):
        return True


@admin.register(Prize)
@with_organization_permissions()
class PrizeAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class AdminAdvisorForm(forms.ModelForm):
        class Meta:
            fields = ("organization", "name", "description", "points")

    list_display = ("name", "description", "organization", "points")
    list_filter = (AdminAdvisorListFilter,)

    def has_add_permission(self, request):
        return True


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
