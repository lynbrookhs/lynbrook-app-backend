from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth.provider import OAuthProvider


class SchoologyAccount(ProviderAccount):
    pass


class SchoologyProvider(OAuthProvider):
    id = "schoology"
    name = "Schoology"
    account_class = SchoologyAccount

    def extract_uid(self, data):
        return data["uid"]

    def extract_common_fields(self, data):
        return {
            "first_name": data["name_first_preferred"] or data["name_first"],
            "last_name": data["name_last"],
            "email": data["primary_email"],
        }

    def get_login_url(self, request, **kwargs):
        return super().get_login_url(request, **kwargs)

    def get_auth_url(self, request, action):
        a = super().get_auth_url(request, action)
        return a


provider_classes = [SchoologyProvider]
