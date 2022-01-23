from django.urls import include, path
from rest_framework_extensions.routers import ExtendedDefaultRouter

from . import views

router = ExtendedDefaultRouter()

users = router.register("users", views.UserViewSet, basename="core-user")
users.register("orgs", views.MembershipViewSet, basename="user-organization", parents_query_lookups=["user"])
users.register("events", views.SubmissionViewSetOld, basename="user-event", parents_query_lookups=["user"])
users.register("submissions", views.SubmissionViewSet, basename="user-submission", parents_query_lookups=["user"])
users.register("tokens", views.ExpoPushTokenViewSet, basename="user-token", parents_query_lookups=["user"])

posts = router.register("posts", views.PostViewSet, basename="post")
polls = posts.register("polls", views.PollViewSet, basename="post-poll", parents_query_lookups=["post"])
polls.register(
    "submissions",
    views.PollSubmissionViewSet,
    basename="post-poll-pollsubmission",
    parents_query_lookups=["post", "poll"],
)

router.register("orgs", views.OrganizationViewSet, basename="organization")
router.register("events", views.EventViewSet, basename="event")
router.register("prizes", views.PrizeViewSet, basename="prize")
router.register("schedules", views.ScheduleViewSet, basename="schedule")

urlpatterns = [
    path("api/schedules/current/", views.CurrentScheduleView.as_view()),
    path("api/schedules/next/", views.NextScheduleView.as_view()),
    path("api/app_version/", views.AppVersionView.as_view()),
    path("api/", include(router.urls)),
    path("", views.IndexView.as_view()),
]
