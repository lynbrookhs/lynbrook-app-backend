from urllib.parse import parse_qsl

import requests
from allauth.socialaccount.providers.oauth.client import (
    OAuthClient,
    OAuthError,
    get_token_prefix,
    get_request_param,
)
from allauth.utils import build_absolute_uri
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from requests_oauthlib import OAuth1


class SchoologyOAuthClient(OAuthClient):
    def _get_request_token(self):
        if self.request_token is None:
            get_params = {}
            if self.parameters:
                get_params.update(self.parameters)
            get_params["oauth_callback"] = build_absolute_uri(self.request, self.callback_url)
            rt_url = self.request_token_url + "?" + urlencode(get_params)
            oauth = OAuth1(self.consumer_key, client_secret=self.consumer_secret)
            response = requests.get(url=rt_url, auth=oauth)
            if response.status_code not in [200, 201]:
                raise OAuthError(
                    _("Invalid response while obtaining request token" ' from "%s".')
                    % get_token_prefix(self.request_token_url)
                )
            self.request_token = dict(parse_qsl(response.text))
            self.request.session[
                "oauth_%s_request_token" % get_token_prefix(self.request_token_url)
            ] = self.request_token
        return self.request_token

    def get_access_token(self):
        if self.access_token is None:
            request_token = self._get_rt_from_session()
            oauth = OAuth1(
                self.consumer_key,
                client_secret=self.consumer_secret,
                resource_owner_key=request_token["oauth_token"],
                resource_owner_secret=request_token["oauth_token_secret"],
            )
            at_url = self.access_token_url
            oauth_verifier = get_request_param(self.request, "oauth_verifier")
            if oauth_verifier:
                at_url = at_url + "?" + urlencode({"oauth_verifier": oauth_verifier})
            response = requests.get(url=at_url, auth=oauth)
            if response.status_code not in [200, 201]:
                raise OAuthError(
                    _("Invalid response while obtaining access token" ' from "%s".')
                    % get_token_prefix(self.request_token_url)
                )
            self.access_token = dict(parse_qsl(response.text))

            self.request.session[
                "oauth_%s_access_token" % get_token_prefix(self.request_token_url)
            ] = self.access_token
        return self.access_token
