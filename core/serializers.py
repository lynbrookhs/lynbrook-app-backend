from django.contrib.auth import get_user_model
from django.db import transaction
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

    @transaction.atomic
    def create(self, validated_data):
        obj, created = self.Meta.model.objects.get_or_create(**validated_data)
        if not created:
            obj.active = True
            obj.save()
        return obj


class ExpoPushTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ExpoPushToken
        fields = ("token",)

    @transaction.atomic
    def create(self, validated_data):
        obj, _ = self.Meta.model.objects.get_or_create(**validated_data)
        return obj


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        fields = (
            "id",
            "url",
            "organization",
            "name",
            "description",
            "start",
            "end",
            "points",
            "submission_type",
            "claimed",
        )

    organization = NestedOrganizationSerializer(read_only=True)
    claimed = serializers.SerializerMethodField()

    def get_claimed(self, event):
        request = self.context.get("request")
        if request:
            return event.users.filter(id=request.user.id).exists()


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Submission
        fields = ("event", "file")

    event = EventSerializer(read_only=True)
    file = serializers.FileField(read_only=True)


class CreateSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Submission
        fields = ("event_id", "event", "file", "code")

    class WrongSubmissionType(Exception):
        pass

    class AlreadyClaimed(Exception):
        pass

    event_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Event.objects.all(), required=False, allow_null=True, write_only=True
    )
    event = EventSerializer(read_only=True)
    file = serializers.FileField(required=False, allow_null=True)
    code = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    @transaction.atomic
    def create(self, validated_data):
        user = validated_data.pop("user")
        code = validated_data.pop("code", None)
        event = validated_data.pop("event_id", None)
        file = validated_data.pop("file", None)

        has_code = code is not None
        has_event = event is not None
        has_file = file is not None
        if not (has_code is not has_event is has_file):
            raise serializers.ValidationError({"code": "Please provide code or both event_id and file."})

        submission_type = models.EventSubmissionType.CODE if has_code else models.EventSubmissionType.FILE
        if submission_type is models.EventSubmissionType.CODE:
            event = models.Event.objects.get(code=code)

        if submission_type != event.submission_type:
            raise self.WrongSubmissionType

        membership, _ = models.Membership.objects.get_or_create(user=user, organization=event.organization)
        membership.points += event.points
        membership.active = True
        membership.save()

        return self.Meta.model.objects.create(event=event, user=user, file=file)


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
