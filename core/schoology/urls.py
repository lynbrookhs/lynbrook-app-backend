from allauth.socialaccount.providers.oauth.urls import default_urlpatterns

from .provider import SchoologyProvider

urlpatterns = default_urlpatterns(SchoologyProvider)
