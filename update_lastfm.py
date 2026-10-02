import json
import os
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USERNAME = "TrickySturluson"
API_KEY = os.environ["LASTFM_API_KEY"]

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "scrobbles.json"
META_FILE = DATA_DIR / "metadata.json"

API_URL = "https://ws.audioscrobbler.com/2.0/"

HEADERS = {
    "User-Agent": "TrickySturluson-LastFM-Stats/1.0"
}


def call_lastfm(params):
    params = {
        **params,
        "api_key": API_KEY,
        "format": "json",
    }

    url = API_URL + "?" + urlencode(params)

    request = Request(url, headers=HEADERS)

    with urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))

    if "error" in data:
        raise RuntimeError(
            f"Last.fm API error {data['error']}: {data.get('message', 'Unknown error')}"
        )

    return data


def load_json(path, default):
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    temp = path.with_suffix(path.suffix + ".tmp")

    with temp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    temp.replace(path)


def normalize_track(track):
    date = track.get("date")

    # Ignore the currently playing track.
    if not date or "uts" not in date:
        return None

    artist = track.get("artist", {})
    album = track.get("album", {})

    return {
        "timestamp": int(date["uts"]),
        "artist": artist.get("#text", ""),
        "artist_mbid": artist.get("mbid", ""),
        "album": album.get("#text", ""),
        "album_mbid": album.get("mbid", ""),
        "track": track.get("name", ""),
        "track_mbid": track.get("mbid", ""),
        "url": track.get("url", ""),
    }


def fetch_new_tracks(since=0):
    tracks = []
    page = 1

    while True:
        print(f"Fetching page {page}...")

        params = {
            "method": "user.getRecentTracks",
            "user": USERNAME,
            "limit": 200,
            "page": page,
        }

        if since:
            params["from"] = since

        data = call_lastfm(params)

        recent = data.get("recenttracks", {})
        raw_tracks = recent.get("track", [])

        if not raw_tracks:
            break

        for track in raw_tracks:
            normalized = normalize_track(track)

            if normalized:
                tracks.append(normalized)

        attr = recent.get("@attr", {})

        total_pages = int(attr.get("totalPages", page))

        if page >= total_pages:
            break

        page += 1

        # Be polite to Last.fm.
        time.sleep(0.25)

    return tracks


def main():
    DATA_DIR.mkdir(exist_ok=True)

    scrobbles = load_json(DATA_FILE, [])
    metadata = load_json(
        META_FILE,
        {
            "username": USERNAME,
            "last_timestamp": 0,
            "total_scrobbles": 0,
        },
    )

    last_timestamp = int(metadata.get("last_timestamp", 0))

    print(f"Existing scrobbles: {len(scrobbles)}")
    print(f"Last timestamp: {last_timestamp}")

    new_tracks = fetch_new_tracks(last_timestamp)

    print(f"Fetched {len(new_tracks)} tracks.")

    existing_keys = {
        (
            track["timestamp"],
            track["artist"],
            track["track"],
        )
        for track in scrobbles
    }

    added = 0

    for track in new_tracks:
        key = (
            track["timestamp"],
            track["artist"],
            track["track"],
        )

        if key not in existing_keys:
            scrobbles.append(track)
            existing_keys.add(key)
            added += 1

    scrobbles.sort(key=lambda x: x["timestamp"])

    if scrobbles:
        metadata["last_timestamp"] = max(
            track["timestamp"] for track in scrobbles
        )

    metadata["total_scrobbles"] = len(scrobbles)
    metadata["last_update"] = int(time.time())

    save_json(DATA_FILE, scrobbles)
    save_json(META_FILE, metadata)

    print(f"Added {added} new scrobbles.")
    print(f"Total scrobbles: {len(scrobbles)}")


if __name__ == "__main__":
    main()
