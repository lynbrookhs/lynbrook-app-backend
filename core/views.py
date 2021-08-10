from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.views.generic.base import TemplateView
from rest_framework import filters, mixins, pagination, status, views, viewsets
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.permissions import NestedUserAccessPolicy, UserAccessPolicy

from . import models, serializers


class IndexView(TemplateView):
    template_name = "index.html"


class SmallPages(pagination.PageNumberPagination):
    page_size = 20


class NestedUserViewSetMixin(NestedViewSetMixin):
    def get_parents_query_dict(self):
        kw = super().get_parents_query_dict()
        for key in ("user", "users"):
            if kw.get(key) == "me":
                kw[key] = self.request.user.id
        return kw

    def get_user(self):
        qdict = self.get_parents_query_dict()
        for key in ("user", "users"):
            try:
                user_id = qdict[key]
                break
            except KeyError:
                pass
        else:
            return None
        return get_user_model().objects.get(pk=user_id)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (UserAccessPolicy,)
    serializer_class = serializers.UserSerializer

    @property
    def access_policy(self):
        return self.permission_classes[0]

    def get_object(self):
        if self.kwargs.get("pk") == "me":
            self.kwargs["pk"] = self.request.user.id
        return super().get_object()

    def get_queryset(self):
        qs = get_user_model().objects.all()
        if self.action == "list":
            return self.access_policy.scope_queryset(self.request, qs)
        else:
            return qs


class MembershipViewSet(
    NestedUserViewSetMixin, viewsets.ReadOnlyModelViewSet, mixins.CreateModelMixin, mixins.DestroyModelMixin
):
    permission_classes = (NestedUserAccessPolicy,)
    queryset = models.Membership.objects.all()
    lookup_field = "organization"
    filter_backends = (filters.OrderingFilter,)
    ordering = ("organization__type", "organization__name")

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.CreateMembershipSerializer
        return serializers.MembershipSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.get_user())

    def handle_exception(self, exc):
        if isinstance(exc, IntegrityError):
            return Response(status=status.HTTP_409_CONFLICT)
        return super().handle_exception(exc)


class UserEventViewSet(NestedUserViewSetMixin, viewsets.ReadOnlyModelViewSet, mixins.CreateModelMixin):
    permission_classes = (NestedUserAccessPolicy,)
    queryset = models.Event.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.ClaimEventSerializer
        return serializers.EventSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.get_user())

    def handle_exception(self, exc):
        if isinstance(exc, models.Event.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if isinstance(exc, serializers.ClaimEventSerializer.AlreadyClaimed):
            return Response(status=status.HTTP_409_CONFLICT)
        return super().handle_exception(exc)


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.OrganizationSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering = ("type", "name")

    def get_queryset(self):
        if "clubs" in self.request.query_params:
            # TODO: Deprecated. Remove when app is updated.
            return models.Organization.objects.filter(type=3)

        if "user" in self.request.query_params:
            # TODO: Deprecated. Remove when app is updated.
            return models.Organization.objects.filter(users=self.request.user)

        return models.Organization.objects.all()


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.PostSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering = ("-date",)
    pagination_class = SmallPages

    def get_queryset(self):
        return models.Post.objects.filter(organization__users=self.request.user)


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.EventSerializer

    def get_queryset(self):
        return models.Event.objects.filter(organization__users=self.request.user)


class PrizeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.PrizeSerializer
    filter_backends = (filters.OrderingFilter,)
    ordering = ("points",)

    def get_queryset(self):
        return models.Prize.objects.filter(organization__users=self.request.user)


class ScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Schedule.objects.all()
    serializer_class = serializers.ScheduleSerializer


class CurrentScheduleView(views.APIView):
    def get(self, request):
        start = date.today() + timedelta(days=2)
        start = start - timedelta(days=start.weekday())
        objects = [models.Schedule.get_for_day(start + timedelta(days=x)) for x in models.DayOfWeek]
        serializer = serializers.NestedScheduleSerializer(objects, context={"request": request}, many=True)
        return Response(
            {
                "start": start,
                "end": start + timedelta(days=6),
                "weekdays": serializer.data,
            }
        )
