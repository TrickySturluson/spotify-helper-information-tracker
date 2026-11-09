#!/usr/bin/env python3
"""Read-only verification of SHIT provider credentials and API connectivity.

Spotify authentication is broker-only: the script obtains a short-lived access token through
GitHub Actions OIDC and never handles a refresh token. Optional providers are reported as skipped
when unconfigured; required providers fail the command.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


TIMEOUT = 20
UA = "SHIT-Credential-Verification/1.0"


def request(url, *, headers=None, data=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})}, data=data)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            body = response.read(256_000)
            return response.status, body, response.headers
    except urllib.error.HTTPError as exc:
        # Do not include response bodies: provider error payloads can echo sensitive
        # request details. Status codes are enough for a useful diagnostic.
        return exc.code, b"", exc.headers
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, b"", {}


def result(name, status, detail, required=False, **extra):
    row = {"provider": name, "status": status, "detail": detail, "required": required}
    row.update(extra)
    return row


def verify_spotify():
    from scripts.spotify.broker_access_token import BrokerTokenError, request_broker_access_token

    try:
        access, _expires_in = request_broker_access_token()
    except BrokerTokenError as exc:
        category = getattr(exc, "category", "broker_error")
        details = {
            "reauthorization_required": "The central broker requires owner-consented Spotify authorization.",
            "rate_limited": "Spotify authentication is rate-limited; respect the broker Retry-After cooldown.",
            "configuration_error": "Spotify rejected the configured broker client credentials.",
            "busy": "Another SHIT workflow is completing the shared credential refresh; retry later.",
        }
        return [result("Spotify", "failed", details.get(category, "The central Spotify authentication broker is unavailable."), True)]
    code, body, _ = request(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": "Bearer " + access},
    )
    if code != 200:
        detail = {
            401: "Spotify rejected the broker-issued access token at /me.",
            403: "Broker-issued token lacks the required account-read permission.",
            429: "Spotify rate-limited the read-only account verification request.",
            0: "Could not reach the Spotify Web API.",
        }.get(code, f"Spotify account endpoint returned HTTP {code}.")
        return [result("Spotify", "failed", detail, True)]
    try:
        profile = json.loads(body.decode("utf-8"))
        if not isinstance(profile, dict) or not isinstance(profile.get("id"), str) or not profile["id"]:
            raise ValueError("missing account identity")
    except (ValueError, AttributeError):
        return [result("Spotify", "failed", "Spotify /v1/me returned no usable account identity.", True)]
    return [result("Spotify", "passed", "Central broker issued a short-lived access token and read-only GET /me succeeded.", True)]


def verify_lastfm():
    key = os.environ.get("LASTFM_API_KEY", "").strip()
    if not key:
        return [result("Last.fm", "missing", "LASTFM_API_KEY is required for the metadata enrichment stages.", True)]
    query = urllib.parse.urlencode({
        "method": "chart.getTopArtists", "api_key": key, "format": "json", "limit": 1,
    })
    code, body, _ = request("https://ws.audioscrobbler.com/2.0/?" + query)
    if code != 200:
        return [result("Last.fm", "failed", f"Last.fm returned HTTP {code or 'network error'}; check the API key and connectivity.", True)]
    try:
        payload = json.loads(body.decode("utf-8"))
    except ValueError:
        payload = {}
    if payload.get("error"):
        return [result("Last.fm", "failed", "Last.fm rejected the API key or request (API error " + str(payload.get("error")) + ").", True)]
    if not isinstance(payload.get("artists", {}).get("artist"), list):
        return [result("Last.fm", "failed", "Last.fm response did not contain the expected chart payload.", True)]
    return [result("Last.fm", "passed", "Authenticated chart.getTopArtists request succeeded.", True)]


def verify_discogs():
    token = os.environ.get("DISCOGS_USER_TOKEN", "").strip()
    if not token:
        return [result("Discogs", "skipped", "Optional DISCOGS_USER_TOKEN is not configured.", False)]
    code, body, _ = request(
        "https://api.discogs.com/oauth/identity",
        headers={"Authorization": "Discogs token=" + token, "Accept": "application/json"},
    )
    if code == 200:
        return [result("Discogs", "passed", "Authenticated read-only /oauth/identity request succeeded.", False)]
    return [result("Discogs", "failed", f"Discogs identity endpoint returned HTTP {code or 'network error'}; check token and connectivity.", False)]


def verify_getsongbpm():
    key = os.environ.get("GETSONGBPM_API_KEY", "").strip()
    if not key:
        return [result("GetSongBPM", "skipped", "Optional GETSONGBPM_API_KEY is not configured.", False)]
    params = urllib.parse.urlencode({"type": "both", "lookup": "song:SHIT credential verification artist:SHIT", "limit": 1})
    code, body, _ = request(
        "https://api.getsong.co/search/?" + params,
        headers={"X-API-KEY": key, "Accept": "application/json"},
    )
    if code == 200:
        try:
            payload = json.loads(body.decode("utf-8"))
        except ValueError:
            payload = {}
        if isinstance(payload, dict) and "search" in payload:
            return [result("GetSongBPM", "passed", "Authenticated read-only search request succeeded.", False)]
        return [result("GetSongBPM", "failed", "GetSongBPM returned an unexpected response shape.", False)]
    return [result("GetSongBPM", "failed", f"GetSongBPM returned HTTP {code or 'network error'}; check API key and connectivity.", False)]


def main():
    checks = []
    for verify in (verify_spotify, verify_lastfm, verify_discogs, verify_getsongbpm):
        try:
            checks.extend(verify())
        except Exception as exc:
            # Exception strings may contain URLs or request metadata; never echo them.
            checks.append(result(verify.__name__.replace("verify_", "").title(), "failed", "Unexpected verification error (" + type(exc).__name__ + ").", False))
    print("SHIT PROVIDER CREDENTIAL VERIFICATION")
    print(json.dumps({"read_only": True, "checks": checks}, indent=2))
    required_failed = any(row["required"] and row["status"] != "passed" for row in checks)
    optional_failed = any(not row["required"] and row["status"] == "failed" for row in checks)
    if required_failed:
        return 2
    if optional_failed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# FILE OVERVIEW
# Purpose: Verify configured SHIT provider credentials before the Great Migration.
# Checks: Broker-issued Spotify access token + read-only /me; Last.fm API key;
#         optional Discogs identity token and GetSongBPM API key.
# Safety: Spotify is broker-only and never reads/refreshes/persists a refresh token. No playlist
#         or canonical Library writes; never prints credential values or provider response bodies.
# Exit: 0 required checks pass; 1 optional configured provider fails; 2 a
#       required provider is missing or invalid.
# Run: python scripts/music/verify_provider_credentials.py
