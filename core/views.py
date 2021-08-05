from django.contrib.auth import get_user_model
from rest_framework import viewsets

from .models import Event, Organization, Post, Prize, Schedule
from .serializers import (
    EventSerializer,
    OrganizationSerializer,
    PostSerializer,
    PrizeSerializer,
    ScheduleSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PostSerializer

    def get_queryset(self):
        return Post.objects.filter(organization__user=self.request.user)


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EventSerializer

    def get_queryset(self):
        return Event.objects.filter(organization__user=self.request.user)


class PrizeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Prize.objects.all()
    serializer_class = PrizeSerializer

    def get_queryset(self):
        return Prize.objects.filter(organization__user=self.request.user)


class ScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
