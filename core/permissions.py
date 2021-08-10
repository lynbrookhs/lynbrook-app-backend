from django.contrib.auth import get_user_model
from rest_access_policy import AccessPolicy


class UserAccessPolicy(AccessPolicy):
    statements = [
        dict(action=["list"], principal="*", effect="allow"),
        dict(action=["retrieve"], principal="*", effect="allow", condition=["is_user"]),
    ]

    def is_user(self, request, view, *args, **kwargs):
        return view.get_object() == request.user

    @classmethod
    def scope_queryset(cls, request, qs):
        return qs.filter(id=request.user.id)


class NestedUserAccessPolicy(AccessPolicy):
    statements = [
        dict(action=["*"], principal="*", effect="allow", condition=["is_user"]),
    ]

    def is_user(self, request, view, *args, **kwargs):
        return view.get_user() == request.user
