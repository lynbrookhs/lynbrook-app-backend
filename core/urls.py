from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_extensions.routers import ExtendedDefaultRouter

from . import views

router = ExtendedDefaultRouter()

users = router.register("users", views.UserViewSet, basename="core-user")
users.register("orgs", views.MembershipViewSet, basename="user-organization", parents_query_lookups=["user"])
users.register("events", views.UserEventViewSet, basename="user-event", parents_query_lookups=["users"])

router.register("orgs", views.OrganizationViewSet, basename="organization")
router.register("posts", views.PostViewSet, basename="post")
router.register("events", views.EventViewSet, basename="event")
router.register("prizes", views.PrizeViewSet, basename="prize")
router.register("schedules", views.ScheduleViewSet, basename="schedule")

urlpatterns = [
    path("api/schedules/current/", views.CurrentScheduleView.as_view()),
    path("api/", include(router.urls)),
    path("", views.IndexView.as_view()),
]
