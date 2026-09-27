import csv
import json
from collections import defaultdict
from datetime import datetime

import qrcode
from datauri import DataURI
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import transaction
from django.http.response import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import path
from django.urls.base import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin
from qrcode.image.svg import SvgPathFillImage

from core.models import *


# The "this school year" points column counts everything from the 1st of this month onward.
# Nothing else is year-specific: the start date and header label roll over on their own each year.
SCHOOL_YEAR_START_MONTH = 8  # August


def school_year_start(today=None):
    """Start of the current school year as an aware datetime (midnight local time)."""
    today = today or timezone.localdate()
    year = today.year if today.month >= SCHOOL_YEAR_START_MONTH else today.year - 1
    return timezone.make_aware(datetime(year, SCHOOL_YEAR_START_MONTH, 1))


def school_year_label(start):
    """e.g. "2026–27 Points" for a year starting Aug 2026."""
    return f"{start.year}–{(start.year + 1) % 100:02d} Points"


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
                            if "organization" in self.fields:
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
        (_("Other"), {"fields": ("wordle_streak",)}),
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
        wrap = self.admin_site.admin_view
        return [
            path("<path:object_id>/points/csv/", wrap(self.points_csv_view), name="core_organization_points_csv"),
            path("<path:object_id>/points/update/", wrap(self.points_update_view), name="core_organization_points_update"),
            path("<path:object_id>/points/", wrap(self.points_view), name="core_organization_points"),
            *super().get_urls(),
        ]

    def get_org_with_points(self, request, object_id):
        # self.get_queryset is scoped to the orgs this user is an admin/advisor of, so anyone else gets DoesNotExist.
        qs = self.get_queryset(request).prefetch_related(
            Prefetch("memberships", Membership.objects.select_related("user").order_by("-points")),
            Prefetch("events", Event.objects.prefetch_related("submissions")),
        )
        org = qs.get(id=object_id)
        if not self.has_view_permission(request, org):
            raise self.model.DoesNotExist
        return org

    def get_events_with_points(self, org):
        return [
            (e, {x.user_id: e.points if x.points is None else x.points for x in e.submissions.all()})
            for e in org.events.all()
        ]

    def get_prior_year_points(self, events, year_start):
        """user_id -> points from events dated before the current school year.

        School-year points are Total minus this, so anything without an event date
        (manual edits to the total) counts toward the current year, and the columns
        always reconcile: Total = prior years + this year.
        """
        prior = defaultdict(int)
        for event, users in events:
            if event.start < year_start:
                for user_id, points in users.items():
                    prior[user_id] += points
        return prior

    @staticmethod
    def year_points(total, prior):
        return max(total - prior, 0)

    def points_view(self, request, object_id):
        try:
            org = self.get_org_with_points(request, object_id)
        except self.model.DoesNotExist:
            return self._get_obj_does_not_exist_redirect(request, self.model._meta, object_id)

        events = self.get_events_with_points(org)
        year_start = school_year_start()
        prior = self.get_prior_year_points(events, year_start)
        context = dict(
            org=org,
            can_edit=self.has_change_permission(request, org),
            update_url=reverse("admin:core_organization_points_update", args=[org.id]),
            year_label=school_year_label(year_start),
            events=[event.name for event, _ in events],
            event_ids=[event.id for event, _ in events],
            members=[
                dict(
                    **membership.user.to_json(),
                    points=membership.points,
                    year_points=self.year_points(membership.points, prior.get(membership.user_id, 0)),
                    events=[users.get(membership.user.id) for event, users in events],
                )
                for membership in org.memberships.all()
            ],
        )

        return render(request, "core/organization_points.html", context)

    def points_update_view(self, request, object_id):
        """Edit a single cell of the points grid.

        Body (JSON): {"user": <user id>, "event": <event id> | null, "points": <int> | null}
        - With "event": creates/updates that user's Submission for the event with a points override,
          or deletes the Submission when "points" is null. The membership total updates via signals.
        - Without "event": sets the membership's total points directly.
        Returns the user's new total, their school-year points, and, for event edits, the value now
        stored for that event cell.
        """
        if request.method != "POST":
            return JsonResponse({"error": "POST required."}, status=405)
        try:
            org = self.get_org_with_points(request, object_id)
        except self.model.DoesNotExist:
            return JsonResponse({"error": "Not found."}, status=404)
        if not self.has_change_permission(request, org):
            return JsonResponse({"error": "You do not have permission to edit points for this organization."}, status=403)

        try:
            body = json.loads(request.body or b"{}")
            user_id = int(body["user"])
            event_id = body.get("event")
            event_id = None if event_id in (None, "") else int(event_id)
            points = body.get("points")
            points = None if points in (None, "") else int(points)
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            return JsonResponse({"error": "Invalid request body."}, status=400)
        if points is not None and points < 0:
            return JsonResponse({"error": "Points cannot be negative."}, status=400)

        with transaction.atomic():
            try:
                membership = Membership.objects.select_for_update().get(organization=org, user_id=user_id)
            except Membership.DoesNotExist:
                return JsonResponse({"error": "That user is not a member of this organization."}, status=400)

            result = {}
            if event_id is None:
                if points is None:
                    return JsonResponse({"error": "Total points cannot be blank."}, status=400)
                membership.points = points
                membership.save(update_fields=("points",))
            else:
                try:
                    event = org.events.get(id=event_id)
                except Event.DoesNotExist:
                    return JsonResponse({"error": "That event does not belong to this organization."}, status=400)

                if points is None:
                    Submission.objects.filter(user_id=user_id, event=event).delete()
                    result["event_points"] = None
                else:
                    submission, _ = Submission.objects.update_or_create(
                        user_id=user_id, event=event, defaults=dict(points=points)
                    )
                    result["event_points"] = submission.get_points()
                membership.refresh_from_db(fields=("points",))

            prior = sum(
                s.get_points()
                for s in Submission.objects.filter(
                    user_id=user_id, event__organization=org, event__start__lt=school_year_start()
                ).select_related("event")
            )
            result["points"] = membership.points
            result["year_points"] = self.year_points(membership.points, prior)
            return JsonResponse(result)

    def points_csv_view(self, request, object_id):
        try:
            org = self.get_org_with_points(request, object_id)
        except self.model.DoesNotExist:
            raise Http404

        events = self.get_events_with_points(org)
        year_start = school_year_start()
        year_label = school_year_label(year_start)
        prior = self.get_prior_year_points(events, year_start)
        response = HttpResponse(
            content_type="text/csv", headers={"Content-Disposition": 'attachment; filename="points.csv"'}
        )
        writer = csv.DictWriter(
            response,
            fieldnames=[
                "id", "email", "first_name", "last_name", "grad_year", "points", year_label,
                *[e.name for e, _ in events],
            ],
        )
        writer.writeheader()
        for membership in org.memberships.all():
            writer.writerow(
                {
                    **membership.user.to_json(),
                    "points": membership.points,
                    year_label: self.year_points(membership.points, prior.get(membership.user_id, 0)),
                    **{event.name: users.get(membership.user.id) for event, users in events},
                }
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
    ordering = ("-start",)

    def get_queryset(self, request):
        # Counting per row would be one query per event; annotating also makes
        # the column sortable, so meetings can be ranked by turnout.
        return super().get_queryset(request).annotate(_user_count=Count("users", distinct=True))

    @admin.display(description="Attendance", ordering="_user_count")
    def user_count(self, obj):
        return obj._user_count

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


@admin.register(Membership)
@with_organization_permissions()
class MembershipAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class AdminAdvisorForm(forms.ModelForm):
        class Meta:
            fields = ("points_spent",)

    list_filter = (AdminAdvisorListFilter,)
    list_display = ("user", "organization", "points", "points_spent", "active")
    search_fields = ("user__first_name", "user__last_name")
    readonly_fields = ("organization", "user", "points", "active")


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
    ordering = ("event", "user")

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


@admin.register(Ping)
@with_organization_permissions()
class PingAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class AdminAdvisorForm(forms.ModelForm):
        class Meta:
            fields = ("organization", "message")

    list_display = ("organization", "message", "sent_by", "created_at")
    list_filter = (AdminAdvisorListFilter,)
    readonly_fields = ("sent_by", "created_at", "instructions")

    @admin.display(description="How pings work")
    def instructions(self, obj):
        return mark_safe(
            """
            <p>Saving a new ping immediately sends it as a push notification to every member of the
            organization who has notifications enabled for it in the Lynbrook App.</p>
            <p>Pings cannot be edited after they are sent.</p>
            """
        )

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ("sent_by", "created_at", "instructions")
        return ("organization", "message", "sent_by", "created_at", "instructions")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.sent_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return True


class SuperuserOnlyAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return False


@admin.register(Memory)
class MemoryAdmin(SuperuserOnlyAdmin):
    """Moderation view for senior memories. Superusers only — photos stay private
    from club admins/advisors. Delete anything inappropriate before release."""

    list_display = ("sender", "short_note", "grad_year", "recipient_count", "created_at")
    list_filter = ("grad_year",)
    search_fields = ("sender__first_name", "sender__last_name", "sender__email", "note")
    readonly_fields = ("sender", "grad_year", "note", "recipients", "created_at", "preview")
    exclude = ("photo",)
    date_hierarchy = "created_at"

    def short_note(self, obj):
        return (obj.note[:60] + "…") if len(obj.note) > 60 else obj.note

    def recipient_count(self, obj):
        return obj.recipients.count()

    @admin.display(description="Photo")
    def preview(self, obj):
        return mark_safe(f'<img src="{obj.photo.url}" style="max-width:480px;max-height:480px;">')


@admin.register(MemoryRelease)
class MemoryReleaseAdmin(SuperuserOnlyAdmin):
    list_display = ("grad_year", "released_at", "released_by")
    readonly_fields = ("grad_year", "released_at", "released_by")


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin, DynamicArrayMixin):
    """Organization events and students' own events in one place.

    Superusers see both. Everyone else sees only their own orgs' events —
    students' personal events (organization is null) never match that filter,
    so club admins cannot read them.
    """

    class AdminAdvisorForm(forms.ModelForm):
        class Meta:
            fields = ("organization", "title", "location", "start", "end", "all_day")

    list_display = ("title", "owner", "location", "start", "end", "all_day")
    list_filter = (AdminAdvisorListFilter,)
    date_hierarchy = "start"
    search_fields = ("title", "location", "organization__name")
    autocomplete_fields = ("user",)

    @admin.display(description="Owner")
    def owner(self, obj):
        return obj.organization or obj.user

    def has_module_permission(self, request):
        return True

    def has_view_permission(self, request, obj=None):
        if obj is None or request.user.is_superuser:
            return True
        if obj.organization is None:
            return False
        return obj.organization.is_admin(request.user) or obj.organization.is_advisor(request.user)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_add_permission(self, request):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("organization", "user")
        if request.user.is_superuser:
            return qs
        return qs.filter(
            Q(organization__admins=request.user) | Q(organization__advisors=request.user)
        ).distinct()

    def get_form(self, request, obj=None, change=False, **kwargs):
        if not request.user.is_superuser:
            class UserForm(self.AdminAdvisorForm):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    q = Q(admins=request.user) | Q(advisors=request.user)
                    if "organization" in self.fields:
                        self.fields["organization"].queryset = (
                            self.fields["organization"].queryset.filter(q).distinct()
                        )

            kwargs["form"] = UserForm

        return super().get_form(request, obj=obj, **kwargs)


@admin.register(WordleEntry)
class WordleEntryAdmin(admin.ModelAdmin, DynamicArrayMixin):
    list_display = ("user", "date", "word", "guesses", "solved")
    search_fields = ("user__first_name", "user__last_name", "word", "guesses")

@admin.register(WordleTheme)
class WordleThemeAdmin(admin.ModelAdmin, DynamicArrayMixin):
    class AdminAdvisorForm(forms.ModelForm):
        class Meta:
            fields = ("date", "word")

@admin.register(ExpoPushToken)
class ExpoPushTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token")
    search_fields = ("user__first_name", "user__last_name", "token")
