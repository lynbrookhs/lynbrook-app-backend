from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.views.generic.base import TemplateView
from rest_framework import filters, pagination, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import models, serializers


class IndexView(TemplateView):
    template_name = "index.html"


class SmallPages(pagination.PageNumberPagination):
    page_size = 20


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer


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
