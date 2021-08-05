from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("orgs", views.OrganizationViewSet)
router.register("posts", views.PostViewSet, basename="post")
router.register("events", views.EventViewSet, basename="event")
router.register("prizes", views.PrizeViewSet, basename="prize")
router.register("schedules", views.ScheduleViewSet)

urlpatterns = [path("", include(router.urls))]
