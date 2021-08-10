from requests import ConnectionError, request
from social_core.backends.oauth import BaseOAuth1
from social_core.exceptions import AuthFailed
from social_core.utils import SSLHttpAdapter, user_agent

API_BASE_URL = "https://api.schoology.com/v1"
SCHOOLOGY_URL = "https://fuhsd.schoology.com"


class SchoologyOAuth(BaseOAuth1):
    """Schoology OAuth authentication backend"""

    name = "schoology"
    ID_KEY = "uid"
    AUTHORIZATION_URL = f"{SCHOOLOGY_URL}/oauth/authorize"
    REQUEST_TOKEN_URL = f"{API_BASE_URL}/oauth/request_token"
    ACCESS_TOKEN_URL = f"{API_BASE_URL}/oauth/access_token"
    REDIRECT_URI_PARAMETER_NAME = "oauth_callback"
    EXTRA_DATA = [
        ("id", "id"),
        ("school_id", "school_id"),
        ("building_id", "building_id"),
        ("username", "username"),
    ]

    USER_DATA_URL = f"{API_BASE_URL}/users/me"
    COURSE_DATA_URL = f"{API_BASE_URL}/users/{{id}}/sections"

    def get_user_details(self, data):
        return {
            "email": data["primary_email"],
            "first_name": data["name_first_preferred"] or data["name_first"],
            "last_name": data["name_last"],
            "grad_year": int(data.get("grad_year", 0)),
            "picture_url": data["picture_url"],
        }

    def user_data(self, access_token, *args, **kwargs):
        user = self.oauth_request(access_token, self.USER_DATA_URL).json()
        # courses = self.oauth_request(access_token, self.COURSE_DATA_URL.format_map(user)).json()
        return user

    def request(self, url, method="GET", *args, **kwargs):
        kwargs.setdefault("headers", {})
        if self.setting("PROXIES") is not None:
            kwargs.setdefault("proxies", self.setting("PROXIES"))

        if self.setting("VERIFY_SSL") is not None:
            kwargs.setdefault("verify", self.setting("VERIFY_SSL"))
        kwargs.setdefault("timeout", self.setting("REQUESTS_TIMEOUT") or self.setting("URLOPEN_TIMEOUT"))
        if self.SEND_USER_AGENT and "User-Agent" not in kwargs["headers"]:
            kwargs["headers"]["User-Agent"] = self.setting("USER_AGENT") or user_agent()

        try:
            response = None
            while response is None or response.status_code == 303:
                if self.SSL_PROTOCOL:
                    session = SSLHttpAdapter.ssl_adapter_session(self.SSL_PROTOCOL)
                    response = session.request(method, url, *args, **kwargs, allow_redirects=False)
                else:
                    response = request(method, url, *args, **kwargs, allow_redirects=False)
                if response.status_code == 303:
                    url = response.headers["Location"]
        except ConnectionError as err:
            raise AuthFailed(self, str(err))
        response.raise_for_status()
        return response
