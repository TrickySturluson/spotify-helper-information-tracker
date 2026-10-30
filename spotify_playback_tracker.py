#!/usr/bin/env python3
"""Locally sample Spotify playback progress and append measured listening intervals.

Uses Spotify OAuth Authorization Code with PKCE and only the
user-read-playback-state scope. No client secret is stored.
"""
import argparse
import base64
import hashlib
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPES = "user-read-playback-state"
TOKEN_FILE = Path(".spotify_token.json")
OUTPUT = Path("playback_data/segments.jsonl")
API = "https://api.spotify.com/v1/me/player"
TOKEN_URL = "https://accounts.spotify.com/api/token"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def save_token(token):
    TOKEN_FILE.write_text(json.dumps(token, indent=2) + "\n", encoding="utf-8")
    try:
        TOKEN_FILE.chmod(0o600)
    except OSError:
        pass


def load_token():
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    return None


def token_request(data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(TOKEN_URL, data=body, headers={
        "Content-Type": "application/x-www-form-urlencoded"
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode())


def authorize():
    if not CLIENT_ID:
        raise SystemExit("Set SPOTIFY_CLIENT_ID to your Spotify Developer app's Client ID.")
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": CLIENT_ID, "response_type": "code",
        "redirect_uri": REDIRECT_URI, "scope": SCOPES,
        "state": state, "code_challenge_method": "S256",
        "code_challenge": challenge,
    }
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    result = {}

    class Callback(BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if query.get("state", [""])[0] != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authorization state mismatch. You can close this window.")
                result["error"] = "OAuth state mismatch"
                return
            if "error" in query:
                result["error"] = query["error"][0]
            else:
                result["code"] = query.get("code", [""])[0]
            self.send_response(200 if "code" in result else 400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Spotify connected. You can close this browser window.")
        def log_message(self, *_):
            pass

    server = HTTPServer(("127.0.0.1", 8888), Callback)
    server.timeout = 180
    print("Opening Spotify authorization in your browser...")
    print("If it does not open, visit:\n" + url)
    webbrowser.open(url)
    server.handle_request()
    server.server_close()
    if "code" not in result:
        raise RuntimeError(result.get("error", "Spotify authorization timed out or was cancelled."))
    token = token_request({
        "client_id": CLIENT_ID, "grant_type": "authorization_code",
        "code": result["code"], "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
    })
    token["obtained_at"] = time.time()
    save_token(token)
    return token


def refresh_token(token):
    refreshed = token_request({
        "client_id": CLIENT_ID, "grant_type": "refresh_token",
        "refresh_token": token["refresh_token"],
    })
    refreshed["refresh_token"] = refreshed.get("refresh_token", token["refresh_token"])
    refreshed["obtained_at"] = time.time()
    save_token(refreshed)
    return refreshed


def access_token(token):
    if time.time() >= token.get("obtained_at", 0) + token.get("expires_in", 3600) - 60:
        token = refresh_token(token)
    return token, token["access_token"]


def get_playback(token):
    token, bearer = access_token(token)
    req = urllib.request.Request(API, headers={"Authorization": "Bearer " + bearer})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return token, json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 204:
            return token, None
        if exc.code == 401:
            token = refresh_token(token)
            req = urllib.request.Request(API, headers={"Authorization": "Bearer " + token["access_token"]})
            with urllib.request.urlopen(req, timeout=20) as response:
                return token, json.loads(response.read().decode())
        if exc.code == 429:
            wait = int(exc.headers.get("Retry-After", "30"))
            print(f"Spotify rate limited the tracker; waiting {wait}s.")
            time.sleep(wait)
            return token, None
        if exc.code == 403:
            raise RuntimeError("Spotify denied playback-state access. Check that the app is authorized for user-read-playback-state.")
        raise


def item_identity(item):
    if not item or item.get("type") != "track":
        return None
    artists = item.get("artists") or []
    return {
        "spotify_id": item.get("id"),
        "spotify_uri": item.get("uri"),
        "track": item.get("name"),
        "artist": ", ".join(a.get("name", "") for a in artists),
        "album": (item.get("album") or {}).get("name"),
        "duration_ms": item.get("duration_ms"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=int, default=10, help="Polling interval in seconds (default: 10; minimum: 5)")
    args = parser.parse_args()
    if args.interval < 5:
        parser.error("Use an interval of at least 5 seconds to avoid excessive API polling.")
    token = load_token() or authorize()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    previous = None
    print(f"Tracking Spotify playback every {args.interval}s. Press Ctrl+C to stop.")
    print(f"Measured intervals will append to {OUTPUT}.")
    try:
        while True:
            sampled_at = time.time()
            try:
                token, state = get_playback(token)
            except urllib.error.HTTPError as exc:
                print(f"Spotify API HTTP {exc.code}; retrying next interval.")
                previous = None
                time.sleep(args.interval)
                continue
            current = None
            if state and state.get("is_playing"):
                identity = item_identity(state.get("item"))
                progress = state.get("progress_ms")
                if identity and progress is not None:
                    current = {"identity": identity, "progress": int(progress), "sampled_at": sampled_at}
            if previous and current and previous["identity"]["spotify_id"] == current["identity"]["spotify_id"]:
                elapsed = sampled_at - previous["sampled_at"]
                progress_delta = current["progress"] - previous["progress"]
                # Progress delta measures playback, not wall time. Reject seeks,
                # resets and stale samples; cap accepted intervals to elapsed time.
                if 0 < progress_delta <= (elapsed + 2.0) * 1000:
                    played_ms = min(progress_delta, int(elapsed * 1000))
                    if played_ms > 0:
                        row = {
                            **current["identity"],
                            "sampled_at": datetime.fromtimestamp(sampled_at, timezone.utc).isoformat(),
                            "played_ms": played_ms,
                            "measurement": "spotify_progress_delta",
                        }
                        with OUTPUT.open("a", encoding="utf-8") as handle:
                            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                        print(f"+{played_ms / 1000:.1f}s  {row['artist']} — {row['track']}")
            previous = current
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nTracker stopped. Recorded intervals are preserved.")


if __name__ == "__main__":
    main()
