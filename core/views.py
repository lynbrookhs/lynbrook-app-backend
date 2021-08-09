from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.http import request
from django.views.generic.base import TemplateView
from rest_access_policy import AccessPolicy
from rest_framework import filters, mixins, pagination, status, views, viewsets
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from . import models, serializers


class IndexView(TemplateView):
    template_name = "index.html"


class SmallPages(pagination.PageNumberPagination):
    page_size = 20


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    class UserAccessPolicy(AccessPolicy):
        statements = [
            dict(action=["list"], principal="*", effect="allow"),
            dict(action=["retrieve"], principal="*", effect="allow", condition=["is_user"]),
        ]

        def is_user(self, request, view, action, *args, **kwargs):
            return view.get_object() == request.user

        @classmethod
        def scope_queryset(cls, request, qs):
            return qs.filter(id=request.user.id)

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
    NestedViewSetMixin, viewsets.ReadOnlyModelViewSet, mixins.CreateModelMixin, mixins.DestroyModelMixin
):
    queryset = models.Membership.objects.all()
    lookup_field = "organization"

    def get_parents_query_dict(self):
        kw = super().get_parents_query_dict()
        if kw["user"] == "me":
            kw["user"] = self.request.user.id
        return kw

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.CreateMembershipSerializer
        return serializers.MembershipSerializer

    def create(self, request, *args, **kwargs):
        qdict = self.get_parents_query_dict()
        user = get_user_model().objects.get(pk=qdict["user"])

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save(user=user)
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.OrganizationSerializer

    def get_queryset(self):
        if "clubs" in self.request.query_params:
            return models.Organization.objects.filter(type=3)
        if "user" in self.request.query_params:
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
