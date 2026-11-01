#!/usr/bin/env python3
"""Read-only verification of SHIT provider credentials and API connectivity.

Never prints, persists, or returns credential values. Optional providers are
reported as skipped when unconfigured; required providers fail the command.
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
    client_id = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    refresh = os.environ.get("SPOTIFY_REFRESH_TOKEN", "").strip()
    if not client_id or not refresh:
        missing = [key for key, value in (("SPOTIFY_CLIENT_ID", client_id), ("SPOTIFY_REFRESH_TOKEN", refresh)) if not value]
        return [result("Spotify", "missing", "Missing " + ", ".join(missing), True)]
    payload = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh,
        "client_id": client_id,
    }).encode()
    code, body, _ = request(
        "https://accounts.spotify.com/api/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=payload,
    )
    if code != 200:
        detail = {
            400: "Refresh token rejected or malformed (check token validity and app pairing).",
            401: "Spotify rejected the client authentication.",
            429: "Spotify rate limited the verification request; retry later.",
            0: "Could not reach Spotify Accounts; check network access.",
        }.get(code, f"Spotify token endpoint returned HTTP {code}.")
        return [result("Spotify", "failed", detail, True)]
    try:
        token_data = json.loads(body.decode("utf-8"))
        access = token_data.get("access_token", "")
    except (ValueError, AttributeError):
        access = ""
        token_data = {}
    if not access:
        return [result("Spotify", "failed", "Token endpoint returned no access token.", True)]
    code, body, _ = request(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": "Bearer " + access},
    )
    if code != 200:
        detail = {
            401: "Access token was issued but Spotify rejected it at /me.",
            403: "Token lacks the required account-read permission.",
            429: "Spotify rate limited the account verification request.",
            0: "Could not reach the Spotify Web API.",
        }.get(code, f"Spotify account endpoint returned HTTP {code}.")
        return [result("Spotify", "failed", detail, True)]
    try:
        profile = json.loads(body.decode("utf-8"))
        account = "authenticated account " + str(profile.get("id") or "(ID unavailable)")
    except (ValueError, AttributeError):
        account = "authenticated account"
    return [result(
        "Spotify", "passed", "Refresh-token exchange and read-only GET /me succeeded; " + account + ".",
        True, refresh_token_rotation_returned=bool(token_data.get("refresh_token")),
    )]


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
# Checks: Spotify refresh-token exchange + read-only /me; Last.fm API key;
#         optional Discogs identity token and GetSongBPM API key.
# Safety: No playlist writes, no library writes, no token persistence, and no
#         credential values or provider response bodies are printed.
# Exit: 0 required checks pass; 1 optional configured provider fails; 2 a
#       required provider is missing or invalid.
# Run: python scripts/music/verify_provider_credentials.py
