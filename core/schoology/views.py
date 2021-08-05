import json

import requests
from allauth.socialaccount.providers.oauth.client import OAuth, OAuthError, get_token_prefix
from allauth.socialaccount.providers.oauth.views import (
    OAuthAdapter,
    OAuthCallbackView,
    OAuthLoginView,
)
from django.utils.translation import gettext as _
from requests_oauthlib.oauth1_auth import OAuth1

from .client import SchoologyOAuthClient
from .provider import SchoologyProvider

API_BASE_URL = "https://api.schoology.com/v1"
SCHOOLOGY_URL = "https://fuhsd.schoology.com"


class SchoologyAPI(OAuth):
    url = f"{API_BASE_URL}/users/me"

    def get_user_info(self):
        return json.loads(self.query(self.url))

    def query(self, url, method="GET", params=None, headers=None):
        req = getattr(requests, method.lower())
        access_token = self._get_at_from_session()
        oauth = OAuth1(
            self.consumer_key,
            client_secret=self.secret_key,
            resource_owner_key=access_token["oauth_token"],
            resource_owner_secret=access_token["oauth_token_secret"],
        )
        response = req(url, auth=oauth, headers=headers, params=params, allow_redirects=False)
        if response.status_code == 303:
            response = req(response.headers["Location"], auth=oauth, headers=headers, params=params)
        if response.status_code != 200:
            raise OAuthError(
                _('No access to private resources at "%s".')
                % get_token_prefix(self.request_token_url)
            )

        return response.text


class SchoologyOAuthAdapter(OAuthAdapter):
    provider_id = SchoologyProvider.id
    request_token_url = f"{API_BASE_URL}/oauth/request_token"
    access_token_url = f"{API_BASE_URL}/oauth/access_token"
    authorize_url = f"{SCHOOLOGY_URL}/oauth/authorize"

    def complete_login(self, request, app, token, response):
        client = SchoologyAPI(request, app.client_id, app.secret, self.request_token_url)
        extra_data = client.get_user_info()
        return self.get_provider().sociallogin_from_response(request, extra_data)


class SchoologyOAuthView(object):
    def _get_client(self, request, callback_url):
        provider = self.adapter.get_provider()
        app = provider.get_app(request)
        scope = " ".join(provider.get_scope(request))
        parameters = {}
        if scope:
            parameters["scope"] = scope
        client = SchoologyOAuthClient(
            request,
            app.client_id,
            app.secret,
            self.adapter.request_token_url,
            self.adapter.access_token_url,
            callback_url,
            parameters=parameters,
            provider=provider,
        )
        return client


class SchoologyOAuthLoginView(SchoologyOAuthView, OAuthLoginView):
    pass


class SchoologyOAuthCallbackView(SchoologyOAuthView, OAuthCallbackView):
    pass


oauth_login = SchoologyOAuthLoginView.adapter_view(SchoologyOAuthAdapter)
oauth_callback = SchoologyOAuthCallbackView.adapter_view(SchoologyOAuthAdapter)
