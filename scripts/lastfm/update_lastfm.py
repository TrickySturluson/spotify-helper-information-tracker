"""Download and maintain the canonical Last.fm scrobble history.

Uses Last.fm recent-track pagination and retry handling. The archive in data/
is the historical source of truth used by downstream analytics; generated
assistant_data files are derived separately.
"""
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


# ============================================================
# Configuration
# ============================================================

USERNAME = "TrickySturluson"

API_URL = "https://ws.audioscrobbler.com/2.0/"

DATA_DIR = "data"
SCROBBLES_FILE = os.path.join(DATA_DIR, "scrobbles.json")
METADATA_FILE = os.path.join(DATA_DIR, "metadata.json")

API_KEY = os.environ.get("LASTFM_API_KEY")

# Last.fm allows up to 200 tracks per request.
PAGE_SIZE = 200

# Small delay between API requests.
REQUEST_DELAY = 0.25

# Number of times to retry temporary failures.
MAX_RETRIES = 6


# ============================================================
# Last.fm API
# ============================================================

def call_lastfm(params, max_retries=MAX_RETRIES):
    """
    Call the Last.fm API with automatic retries for temporary
    server/network errors.
    """

    headers = {
        "User-Agent": "TrickyLastFM/1.0 (Last.fm history importer)"
    }

    for attempt in range(max_retries):
        try:
            query = urlencode(params)

            request = Request(
                f"{API_URL}?{query}",
                headers=headers
            )

            with urlopen(request, timeout=30) as response:
                data = json.loads(
                    response.read().decode("utf-8")
                )

            # Last.fm can return HTTP 200 while still reporting
            # an API-level error.
            if "error" in data:
                error_code = str(data.get("error"))
                error_message = data.get(
                    "message",
                    "Unknown Last.fm error"
                )

                # Temporary Last.fm errors.
                if error_code in {"11", "16", "29"}:
                    wait_time = 2 ** attempt

                    print(
                        f"Last.fm temporary error {error_code}: "
                        f"{error_message}"
                    )
                    print(
                        f"Retrying in {wait_time} seconds "
                        f"(attempt {attempt + 1}/{max_retries})..."
                    )

                    time.sleep(wait_time)
                    continue

                # Permanent API error.
                raise RuntimeError(
                    f"Last.fm API error {error_code}: "
                    f"{error_message}"
                )

            return data

        except HTTPError as e:
            # These are generally temporary server-side errors.
            if e.code in {500, 502, 503, 504}:
                wait_time = 2 ** attempt

                print(
                    f"Last.fm returned HTTP {e.code}."
                )
                print(
                    f"Retrying in {wait_time} seconds "
                    f"(attempt {attempt + 1}/{max_retries})..."
                )

                time.sleep(wait_time)
                continue

            # Other HTTP errors are probably actual request/config
            # problems, so don't hide them.
            raise

        except (URLError, TimeoutError) as e:
            wait_time = 2 ** attempt

            print(
                f"Network error: {e}"
            )
            print(
                f"Retrying in {wait_time} seconds "
                f"(attempt {attempt + 1}/{max_retries})..."
            )

            time.sleep(wait_time)

    raise RuntimeError(
        f"Last.fm request failed after "
        f"{max_retries} attempts."
    )


# ============================================================
# Load existing data
# ============================================================

def load_json(path, default):
    """
    Load JSON from disk. Return default if the file doesn't exist.
    """

    if not os.path.exists(path):
        return default

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# Fetch tracks
# ============================================================

def fetch_new_tracks(last_timestamp):
    """
    Fetch scrobbles from Last.fm after last_timestamp.

    If last_timestamp is None, fetch the entire available history.
    """

    tracks = []
    page = 1

    while True:
        params = {
            "method": "user.getRecentTracks",
            "user": USERNAME,
            "api_key": API_KEY,
            "format": "json",
            "limit": PAGE_SIZE,
            "page": page,
        }

        # Only use "from" once we already have existing data.
        if last_timestamp:
            params["from"] = last_timestamp

        print(f"Fetching Last.fm page {page}...")

        data = call_lastfm(params)

        recent_tracks = data.get("recenttracks", {})
        page_tracks = recent_tracks.get("track", [])

        if not page_tracks:
            break

        # Last.fm may return a dictionary instead of a list when
        # only one track exists.
        if isinstance(page_tracks, dict):
            page_tracks = [page_tracks]

        page_count = 0

        for track in page_tracks:

            # Ignore the currently playing track.
            if track.get("@attr", {}).get("nowplaying") == "true":
                continue

            date_info = track.get("date")

            # Tracks without a date are generally the now-playing
            # entry or otherwise incomplete.
            if not date_info:
                continue

            timestamp = date_info.get("uts")

            if not timestamp:
                continue

            timestamp = int(timestamp)

            # If we're updating an existing database, don't pull
            # anything older than the last known timestamp.
            if last_timestamp and timestamp <= int(last_timestamp):
                continue

            artist_info = track.get("artist", {}) or {}
            album_info = track.get("album", {}) or {}

            artist = artist_info.get("#text", "")
            artist_mbid = artist_info.get("mbid", "")

            album = album_info.get("#text", "")
            album_mbid = album_info.get("mbid", "")

            track_name = track.get("name", "")
            track_mbid = track.get("mbid", "")

            url = track.get("url", "")

            normalized = {
                "timestamp": timestamp,
                "artist": artist,
                "artist_mbid": artist_mbid,
                "album": album,
                "album_mbid": album_mbid,
                "track": track_name,
                "track_mbid": track_mbid,
                "url": url,
            }

            tracks.append(normalized)
            page_count += 1

        print(
            f"  Added {page_count} new tracks from page {page}."
        )

        # Determine how many pages Last.fm says exist.
        attr = recent_tracks.get("@attr", {})

        try:
            total_pages = int(attr.get("totalPages", page))
        except (TypeError, ValueError):
            total_pages = page

        if page >= total_pages:
            break

        # If we're doing an incremental update and this page
        # contained only tracks older than our timestamp, we're done.
        if last_timestamp and page_count == 0:
            break

        page += 1

        time.sleep(REQUEST_DELAY)

    return tracks


# ============================================================
# Deduplicate
# ============================================================

def deduplicate_tracks(tracks):
    """
    Remove duplicate scrobbles.

    Last.fm timestamps are normally unique enough for this,
    but artist + track are included as additional protection.
    """

    seen = set()
    unique_tracks = []

    for track in tracks:
        key = (
            track.get("timestamp"),
            track.get("artist", ""),
            track.get("track", "")
        )

        if key in seen:
            continue

        seen.add(key)
        unique_tracks.append(track)

    return unique_tracks


# ============================================================
# Main
# ============================================================

def main():

    if not API_KEY:
        raise RuntimeError(
            "LASTFM_API_KEY environment variable is missing."
        )

    os.makedirs(DATA_DIR, exist_ok=True)

    print("=" * 60)
    print("Last.fm History Updater")
    print("=" * 60)
    print(f"Username: {USERNAME}")
    print()

    # --------------------------------------------------------
    # Load existing scrobbles
    # --------------------------------------------------------

    existing_tracks = load_json(
        SCROBBLES_FILE,
        []
    )

    metadata = load_json(
        METADATA_FILE,
        {}
    )

    print(
        f"Existing scrobbles in database: "
        f"{len(existing_tracks)}"
    )

    # --------------------------------------------------------
    # Determine last timestamp
    # --------------------------------------------------------

    last_timestamp = metadata.get("last_timestamp")

    if last_timestamp:
        print(
            f"Last known timestamp: {last_timestamp}"
        )
        print("Fetching new scrobbles...")
    else:
        print(
            "No previous timestamp found."
        )
        print(
            "This appears to be the initial import."
        )
        print(
            "Fetching full Last.fm history..."
        )

    print()

    # --------------------------------------------------------
    # Fetch new tracks
    # --------------------------------------------------------

    new_tracks = fetch_new_tracks(last_timestamp)

    print()
    print(
        f"New scrobbles fetched: {len(new_tracks)}"
    )

    # --------------------------------------------------------
    # Combine old + new data
    # --------------------------------------------------------

    all_tracks = existing_tracks + new_tracks

    print(
        f"Total before deduplication: "
        f"{len(all_tracks)}"
    )

    all_tracks = deduplicate_tracks(all_tracks)

    # Sort oldest → newest.
    all_tracks.sort(
        key=lambda track: track.get("timestamp", 0)
    )

    print(
        f"Total after deduplication: "
        f"{len(all_tracks)}"
    )

    # --------------------------------------------------------
    # Determine newest timestamp
    # --------------------------------------------------------

    if all_tracks:
        newest_timestamp = max(
            int(track["timestamp"])
            for track in all_tracks
            if track.get("timestamp")
        )
    else:
        newest_timestamp = last_timestamp

    # --------------------------------------------------------
    # Save scrobbles
    # --------------------------------------------------------

    with open(
        SCROBBLES_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            all_tracks,
            f,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # Save metadata
    # --------------------------------------------------------

    metadata = {
        "username": USERNAME,
        "last_timestamp": newest_timestamp,
        "total_scrobbles": len(all_tracks),
        "last_updated": int(time.time()),
    }

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            metadata,
            f,
            indent=2
        )

    # --------------------------------------------------------
    # Done
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("SUCCESS")
    print("=" * 60)
    print(
        f"Total scrobbles stored: {len(all_tracks)}"
    )
    print(
        f"Newest timestamp: {newest_timestamp}"
    )
    print(
        f"Saved to: {SCROBBLES_FILE}"
    )
    print(
        f"Metadata saved to: {METADATA_FILE}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
