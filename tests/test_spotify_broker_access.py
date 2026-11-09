import json
import unittest

from scripts.spotify.broker_access_token import BrokerTokenError, request_broker_access_token


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = json.dumps(payload).encode()
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit=-1):
        return self.payload


class BrokerAccessTokenTests(unittest.TestCase):
    def setUp(self):
        self.environ = {
            "ACTIONS_ID_TOKEN_REQUEST_URL": "https://pipelines.actions.githubusercontent.com/oidc?api-version=2.0",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "github-oidc-request-secret",
            "SHIT_AUTH_BROKER_URL": "https://auth.example.workers.dev",
        }
        self.calls = []

    def opener(self, response_payload):
        def open_request(request, timeout=0):
            self.calls.append((request, timeout))
            if len(self.calls) == 1:
                return FakeResponse({"value": "signed-github-oidc-jwt"})
            return FakeResponse(response_payload)
        return open_request

    def test_requests_dedicated_oidc_audience_and_returns_only_access_token(self):
        token, expires = request_broker_access_token(
            self.environ,
            self.opener({"accessToken": "spotify-short-lived-access-token", "expiresIn": 3600, "accountId": "spotifyuser"}),
        )
        self.assertEqual(token, "spotify-short-lived-access-token")
        self.assertEqual(expires, 3600)
        oidc_request, oidc_timeout = self.calls[0]
        self.assertIn("audience=shit-spotify-refresh", oidc_request.full_url)
        self.assertEqual(oidc_request.get_header("Authorization"), "Bearer github-oidc-request-secret")
        broker_request, broker_timeout = self.calls[1]
        self.assertEqual(broker_request.full_url, "https://auth.example.workers.dev/internal/spotify/refresh")
        self.assertEqual(broker_request.get_method(), "POST")
        self.assertEqual(broker_request.get_header("Authorization"), "Bearer signed-github-oidc-jwt")
        self.assertEqual(set(json.loads(broker_request.data)), {"operationId"})
        self.assertEqual(len(json.loads(broker_request.data)["operationId"]), 43)
        self.assertEqual((oidc_timeout, broker_timeout), (15, 15))

    def test_missing_oidc_or_broker_configuration_fails_closed(self):
        for key in ("ACTIONS_ID_TOKEN_REQUEST_URL", "ACTIONS_ID_TOKEN_REQUEST_TOKEN", "SHIT_AUTH_BROKER_URL"):
            env = dict(self.environ)
            env.pop(key)
            with self.subTest(key=key), self.assertRaises(BrokerTokenError):
                request_broker_access_token(env, self.opener({"accessToken": "unused", "expiresIn": 3600}))

    def test_non_https_broker_url_is_rejected(self):
        env = dict(self.environ, SHIT_AUTH_BROKER_URL="http://auth.example.workers.dev")
        with self.assertRaises(BrokerTokenError):
            request_broker_access_token(env, self.opener({"accessToken": "unused", "expiresIn": 3600}))

    def test_refresh_token_material_is_never_accepted_from_broker_response(self):
        with self.assertRaises(BrokerTokenError):
            request_broker_access_token(
                self.environ,
                self.opener({
                    "accessToken": "spotify-short-lived-access-token",
                    "expiresIn": 3600,
                    "refreshToken": "must-never-be-returned",
                }),
            )

    def test_invalid_access_token_lifetime_is_rejected(self):
        for expires in (0, 59, 86_401, True, "3600"):
            with self.subTest(expires=expires), self.assertRaises(BrokerTokenError):
                request_broker_access_token(
                    self.environ,
                    self.opener({"accessToken": "spotify-short-lived-access-token", "expiresIn": expires}),
                )


if __name__ == "__main__":
    unittest.main()


# -----------------------------------------------------------------------------
# FILE OVERVIEW
# Purpose: Test the GitHub Actions OIDC client used to obtain broker-issued Spotify access tokens.
# Coverage: OIDC audience, HTTPS validation, payload minimization, refresh-token rejection, and expiry.
# Safety: Uses fake responses only; no GitHub, Cloudflare, or Spotify credentials or network calls.
# Related: scripts/spotify/broker_access_token.py, auth-broker/src/index.js.
# -----------------------------------------------------------------------------
