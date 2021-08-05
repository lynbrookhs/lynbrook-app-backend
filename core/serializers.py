from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Event, Organization, Period, Poll, Post, Prize, Schedule, SchedulePeriod


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "first_name", "last_name", "grad_year", "is_staff", "is_superuser")


class BaseOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "url", "name", "type", "advisors", "admins", "day", "time", "link")


class OrganizationSerializer(BaseOrganizationSerializer):
    advisors = UserSerializer(many=True, read_only=True)
    admins = UserSerializer(many=True, read_only=True)


class PollSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poll
        fields = ("post", "type", "description", "choices", "min_values", "max_values")


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("organization", "title", "date", "content", "published", "polls")

    organization = BaseOrganizationSerializer(read_only=True)
    polls = PollSerializer(many=True, read_only=True)


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ("organization", "name", "description", "start", "end", "points", "code")

    organization = BaseOrganizationSerializer(read_only=True)


class PrizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prize
        fields = ("organization", "name", "description", "points")

    organization = BaseOrganizationSerializer(read_only=True)


class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        fields = ("id", "name", "customizable")


class SchedulePeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedulePeriod
        fields = ("start", "end", "period")

    period = PeriodSerializer()


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ("start", "end", "weekday", "periods", "priority")

    periods = SchedulePeriodSerializer(many=True, read_only=True)
