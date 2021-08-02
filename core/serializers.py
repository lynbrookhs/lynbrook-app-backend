from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Organization


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "is_superuser", "username", "first_name", "last_name")


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "url", "name", "type", "advisors", "admins", "day", "time", "link")
        depth = 1
