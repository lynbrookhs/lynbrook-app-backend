from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("organizations", views.OrganizationViewSet)
router.register("users", views.UserViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
