"""Fetch a short-lived Spotify access token from the SHIT OIDC broker.

This helper deliberately has no refresh-token or legacy-secret fallback. It is
intended for GitHub Actions jobs after the broker endpoint is deployed and the
exact workflow identity has been allowlisted.
"""
from __future__ import annotations

import json
import os
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request

MAX_RESPONSE_BYTES = 16_384
OIDC_AUDIENCE = "shit-spotify-refresh"


class BrokerTokenError(RuntimeError):
    pass


def _read_json(opener, request: urllib.request.Request) -> dict:
    try:
        with opener(request, timeout=15) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                raise BrokerTokenError("Authentication broker response was too large.")
            status = getattr(response, "status", 200)
            if status < 200 or status >= 300:
                raise BrokerTokenError("Authentication broker request failed.")
    except urllib.error.HTTPError as exc:
        raise BrokerTokenError("Authentication broker request failed.") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise BrokerTokenError("Authentication broker is unavailable.") from exc
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise BrokerTokenError("Authentication broker returned an invalid response.") from exc
    if not isinstance(value, dict):
        raise BrokerTokenError("Authentication broker returned an invalid response.")
    return value


def request_broker_access_token(environ=None, opener=urllib.request.urlopen):
    env = os.environ if environ is None else environ
    oidc_url = str(env.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")).strip()
    oidc_request_token = str(env.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")).strip()
    broker_base = str(env.get("SHIT_AUTH_BROKER_URL", "")).strip().rstrip("/")
    if not oidc_url or not oidc_request_token or not broker_base or "\\n" in oidc_request_token or "\\r" in oidc_request_token:
        raise BrokerTokenError("GitHub OIDC or SHIT broker configuration is missing.")

    parsed_oidc = urllib.parse.urlsplit(oidc_url)
    parsed_broker = urllib.parse.urlsplit(broker_base)
    if parsed_oidc.scheme != "https" or not parsed_oidc.netloc:
        raise BrokerTokenError("GitHub OIDC endpoint must use HTTPS.")
    if parsed_broker.scheme != "https" or not parsed_broker.netloc or parsed_broker.path not in ("", "/") or parsed_broker.query or parsed_broker.fragment or parsed_broker.username or parsed_broker.password:
        raise BrokerTokenError("SHIT authentication broker URL must be a canonical HTTPS origin.")

    query = urllib.parse.parse_qsl(parsed_oidc.query, keep_blank_values=True)
    query = [(key, value) for key, value in query if key != "audience"]
    query.append(("audience", OIDC_AUDIENCE))
    oidc_target = urllib.parse.urlunsplit(parsed_oidc._replace(query=urllib.parse.urlencode(query)))
    oidc_request = urllib.request.Request(
        oidc_target,
        headers={"Authorization": "Bearer " + oidc_request_token, "Accept": "application/json"},
    )
    oidc_data = _read_json(opener, oidc_request)
    oidc_jwt = oidc_data.get("value")
    if not isinstance(oidc_jwt, str) or not oidc_jwt or "\n" in oidc_jwt:
        raise BrokerTokenError("GitHub did not issue a usable workload identity.")

    operation_id = secrets.token_urlsafe(32)
    payload = json.dumps({"operationId": operation_id}, separators=(",", ":")).encode()
    broker_request = urllib.request.Request(
        broker_base + "/internal/spotify/refresh",
        data=payload,
        headers={
            "Authorization": "Bearer " + oidc_jwt,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    broker_data = _read_json(opener, broker_request)
    access_token = broker_data.get("accessToken")
    expires_in = broker_data.get("expiresIn")
    if "refreshToken" in broker_data or not isinstance(access_token, str) or not access_token or "\n" in access_token:
        raise BrokerTokenError("SHIT broker did not return a valid short-lived access token.")
    if not isinstance(expires_in, int) or isinstance(expires_in, bool) or not 60 <= expires_in <= 86_400:
        raise BrokerTokenError("SHIT broker returned an invalid access-token lifetime.")
    return access_token, expires_in


def main():
    try:
        access_token, expires_in = request_broker_access_token()
        env_file = os.environ.get("GITHUB_ENV", "").strip()
        if not env_file:
            raise BrokerTokenError("GITHUB_ENV is unavailable; refusing to print the access token.")
        # GitHub masks the token before any later step can accidentally echo it.
        print("::add-mask::" + access_token)
        with open(env_file, "a", encoding="utf-8") as handle:
            handle.write("SHIT_BROKER_ACCESS_TOKEN=" + access_token + "\n")
            handle.write("SHIT_BROKER_ACCESS_TOKEN_EXPIRES_IN=" + str(expires_in) + "\n")
    except BrokerTokenError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
