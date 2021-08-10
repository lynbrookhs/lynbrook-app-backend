from django.contrib.auth import get_user_model
from rest_framework import serializers

from . import models

# Nested


class NestedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "first_name", "last_name")


class NestedOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Organization
        fields = ("id", "name", "type")


class NestedPollSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Poll
        fields = ("id", "type", "description", "choices", "min_values", "max_values")


class NestedMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Membership
        fields = ("organization", "points")

    organization = NestedOrganizationSerializer(read_only=True)


class NestedPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Period
        fields = ("id", "name", "customizable")


class NestedSchedulePeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SchedulePeriod
        fields = ("start", "end", "period")

    period = NestedPeriodSerializer()


class NestedScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Schedule
        fields = ("id", "url", "name", "periods")

    periods = NestedSchedulePeriodSerializer(many=True, read_only=True)


# Main


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "picture_url",
            "grad_year",
            "is_staff",
            "is_superuser",
            "memberships",
        )

    memberships = NestedMembershipSerializer(many=True, read_only=True)


class OrganizationLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrganizationLink
        fields = ("title", "url")


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Organization
        fields = (
            "id",
            "url",
            "name",
            "type",
            "advisors",
            "admins",
            "day",
            "time",
            "link",
            "ical_links",
            "description",
            "category",
            "links",
        )

    advisors = NestedUserSerializer(many=True, read_only=True)
    admins = NestedUserSerializer(many=True, read_only=True)
    links = OrganizationLinkSerializer(many=True, read_only=True)


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Post
        fields = ("id", "url", "organization", "title", "date", "content", "published", "polls")

    organization = NestedOrganizationSerializer(read_only=True)
    polls = NestedPollSerializer(many=True, read_only=True)


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Membership
        fields = ("organization", "points")

    organization = OrganizationSerializer(read_only=True)
    points = serializers.IntegerField(read_only=True)


class CreateMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Membership
        fields = ("organization", "points")

    points = serializers.IntegerField(read_only=True)


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        fields = ("id", "url", "organization", "name", "description", "start", "end", "points")

    organization = NestedOrganizationSerializer(read_only=True)


class ClaimEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        fields = ("id", "url", "organization", "name", "description", "start", "end", "code", "points")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != "code":
                self.fields[field].read_only = True

    def create(self, validated_data):
        code = validated_data["code"]
        event = self.Meta.model.objects.get(code=code)
        event.users.add(validated_data["user"])
        return event


class PrizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Prize
        fields = ("id", "url", "organization", "name", "description", "points")

    organization = NestedOrganizationSerializer(read_only=True)


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Schedule
        fields = ("id", "url", "name", "start", "end", "weekday", "periods", "priority")

    periods = NestedSchedulePeriodSerializer(many=True, read_only=True)
