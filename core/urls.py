from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("users", views.UserViewSet)
router.register("orgs", views.OrganizationViewSet)
router.register("posts", views.PostViewSet)
router.register("polls", views.PollViewSet)
router.register("events", views.EventViewSet)
router.register("prizes", views.PrizeViewSet)
router.register("schedules", views.ScheduleViewSet)

urlpatterns = [path("", include(router.urls))]
