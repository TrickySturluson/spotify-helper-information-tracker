#!/usr/bin/env python3
"""Canonical song library with lazy reads and stable identity aliases."""
import hashlib
import json
import re
from pathlib import Path

DEFAULT_ROOT = Path("assistant_data/music/library")
INDEX_NAME = "library_index.json"


def norm(value):
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def digest(value, length=20):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:length]


def safe_id(value):
    value = str(value or "").strip().casefold()
    if value.startswith("mbid:"):
        return "mbid-" + re.sub(r"[^a-z0-9-]", "", value[5:])
    if value.startswith("spotify:"):
        return "spotify-" + re.sub(r"[^a-z0-9]", "", value.split(":")[-1])
    return re.sub(r"[^a-z0-9_-]", "-", value).strip("-") or "unknown"


def artist_key(row):
    candidate = str(row.get("artist_mbid") or row.get("artist_id") or "").strip().casefold()
    if candidate.startswith(("mbid:", "name:")):
        return candidate
    if candidate and re.fullmatch(r"[0-9a-f-]{36}", candidate):
        return "mbid:" + candidate
    return "name:" + digest(norm(row.get("artist")))


def album_key(row, aid):
    candidate = str(row.get("album_mbid") or row.get("release_mbid") or "").strip().casefold()
    if candidate:
        return "mbid:" + candidate if not candidate.startswith("mbid:") else candidate
    album = row.get("album") or row.get("album_name")
    if not album:
        return None
    return "album:" + digest(aid + "\0" + norm(album))


def recording_key(row, aid, bid):
    candidate = str(row.get("track_mbid") or row.get("recording_mbid") or "").strip().casefold()
    source_id = str(row.get("track_id") or "").strip().casefold()
    if not candidate and source_id.startswith("mbid:"):
        candidate = source_id[5:]
    if candidate:
        return "mbid:" + candidate if not candidate.startswith("mbid:") else candidate
    sid = str(row.get("spotify_id") or row.get("spotify_track_id") or "").strip()
    if not sid and source_id.startswith("spotify:track:"):
        sid = source_id
    if sid.startswith("spotify:track:"):
        sid = sid.rsplit(":", 1)[-1]
    if sid:
        return "spotify:" + sid.casefold()
    # A stable source-profile key is not a verified recording ID, but it keeps
    # same-title releases distinct when the source contains no release/duration.
    if source_id.startswith("track:"):
        return "source:" + source_id[6:]
    duration = row.get("duration_ms") or row.get("duration") or ""
    return "fallback:" + digest((aid or "") + "\0" + (bid or "") + "\0" + norm(row.get("track") or row.get("name")) + "\0" + str(duration))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    tmp.replace(path)


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None



def select_recent_track_rows(track_rows, recent_rows, limit):
    """Select a bounded, deduplicated recent batch without making provider calls."""
    if not isinstance(track_rows, dict) or not isinstance(recent_rows, list):
        return {}, {"selected": 0, "unmatched": 0, "duplicates": 0}
    by_mbid, by_track_id = {}, {}
    for row in track_rows.values():
        if not isinstance(row, dict):
            continue
        if row.get("track_id"):
            by_track_id[str(row["track_id"]).casefold()] = row
        mbid = str(row.get("track_mbid") or row.get("recording_mbid") or "").strip().casefold()
        if mbid:
            current = by_mbid.get(mbid)
            score = sum(len(row.get(field) or []) for field in ("lastfm_tags", "musicbrainz_tags", "musicbrainz_genres"))
            current_score = sum(len(current.get(field) or []) for field in ("lastfm_tags", "musicbrainz_tags", "musicbrainz_genres")) if current else -1
            if score > current_score:
                by_mbid[mbid] = row
    selected, seen = {}, set()
    unmatched = duplicates = 0
    for recent in recent_rows:
        if not isinstance(recent, dict):
            continue
        mbid = str(recent.get("track_mbid") or "").strip().casefold()
        track_id = str(recent.get("track_id") or "").strip().casefold()
        row = by_mbid.get(mbid) if mbid else None
        row = row or by_track_id.get(track_id)
        if not row:
            unmatched += 1
            continue
        identity = mbid or str(row.get("track_id") or track_id).casefold()
        if identity in seen:
            duplicates += 1
            continue
        seen.add(identity)
        enriched = dict(row)
        enriched["listening_context"] = {
            "source": "Last.fm scrobble archive",
            "recent_plays": recent.get("recent_plays"),
            "all_time_plays": recent.get("all_time_plays"),
        }
        selected[str(row.get("track_id") or identity)] = enriched
        if len(selected) >= limit:
            break
    return selected, {"selected": len(selected), "unmatched": unmatched, "duplicates": duplicates}


class MusicLibrary:
    """Index-backed lazy resolver; song JSON remains the canonical evidence."""

    def __init__(self, root=DEFAULT_ROOT):
        self.root = Path(root)
        self.index_path = self.root / INDEX_NAME
        self.index = read_json(self.index_path) or {
            "schema_version": 1, "songs": {}, "spotify_ids": {},
            "recording_mbids": {}, "name_candidates": {}, "artists": {}, "albums": {},
        }

    def path_for(self, kind, key):
        safe = safe_id(key)
        filename = {"artists": "artist.json", "albums": "album.json", "songs": "song.json"}[kind]
        return self.root / kind / safe[:2] / safe / filename

    def get_song(self, spotify_id=None, recording_mbid=None, artist=None, track=None, album=None):
        key = None
        if spotify_id:
            key = self.index.get("spotify_ids", {}).get(str(spotify_id).rsplit(":", 1)[-1].casefold())
        if key is None and recording_mbid:
            key = self.index.get("recording_mbids", {}).get(str(recording_mbid).casefold())
        if key is None and artist and track:
            alias = norm(artist) + "\0" + norm(track)
            candidates = self.index.get("name_candidates", {}).get(alias)
            if candidates is None:  # Read indexes written by the early prototype.
                candidates = self.index.get("name_candidates", {}).get(norm(artist) + "\\0" + norm(track), [])
            if len(candidates) == 1:
                key = candidates[0]
            elif album:
                entries = self.index.get("songs", self.index.get("recordings", {}))
                matches = [x for x in candidates if norm(entries.get(x, {}).get("album")) == norm(album)]
                if len(matches) == 1:
                    key = matches[0]
        entries = self.index.get("songs", self.index.get("recordings", {}))
        if key is None or key not in entries:
            return None
        record = read_json(self.root / entries[key]["path"])
        if not isinstance(record, dict):
            return None
        relations = record.get("relations", {})
        artist_record = read_json(self.root / relations["artist_path"]) if relations.get("artist_path") else None
        album_record = read_json(self.root / relations["album_path"]) if relations.get("album_path") else None
        return {"song": record, "artist": artist_record or {}, "album": album_record or {}}

    # Backward-compatible method name for existing callers.
    get_recording = get_song


    def audit(self):
        """Check index aliases and every referenced song/artist/album record."""
        errors = []
        songs = self.index.get("songs", self.index.get("recordings", {}))
        artists = self.index.get("artists", {})
        albums = self.index.get("albums", {})
        if not isinstance(songs, dict) or not isinstance(artists, dict) or not isinstance(albums, dict):
            return {"ok": False, "errors": ["index collections must be objects"], "songs": 0, "artists": 0, "albums": 0}
        for song_id, entry in songs.items():
            if not isinstance(entry, dict) or not entry.get("path"):
                errors.append(f"song index entry is malformed: {song_id}")
                continue
            record = read_json(self.root / entry["path"])
            if not isinstance(record, dict):
                errors.append(f"song record is missing or invalid: {song_id}")
                continue
            if record.get("id") != song_id:
                errors.append(f"song record ID mismatch: {song_id}")
            identity = record.get("identity") or {}
            if not identity.get("artist") or not identity.get("title"):
                errors.append(f"song identity is missing artist/title: {song_id}")
            relations = record.get("relations") or {}
            artist_path = relations.get("artist_path")
            artist_record = read_json(self.root / artist_path) if artist_path else None
            if not isinstance(artist_record, dict):
                errors.append(f"related artist record is missing: {song_id}")
            elif artist_record.get("id") != identity.get("artist_id"):
                errors.append(f"related artist identity mismatch: {song_id}")
            album_path = relations.get("album_path")
            if album_path:
                album_record = read_json(self.root / album_path)
                if not isinstance(album_record, dict):
                    errors.append(f"related album record is missing: {song_id}")
                elif album_record.get("id") != identity.get("album_id"):
                    errors.append(f"related album identity mismatch: {song_id}")
        for alias, candidates in self.index.get("name_candidates", {}).items():
            if not isinstance(candidates, list) or not candidates:
                errors.append(f"name alias has no candidate list: {alias!r}")
                continue
            if any(candidate not in songs for candidate in candidates):
                errors.append(f"name alias references missing song: {alias!r}")
        for alias_map_name in ("spotify_ids", "recording_mbids"):
            for alias, song_id in self.index.get(alias_map_name, {}).items():
                if song_id not in songs:
                    errors.append(f"{alias_map_name} alias references missing song: {alias}")
        return {
            "ok": not errors, "errors": errors,
            "songs": len(songs), "artists": len(artists), "albums": len(albums),
        }

    def put_catalogue(self, track_rows, artist_rows=None, album_rows=None, audio_rows=None, lyric_rows=None):
        artists = artist_rows if isinstance(artist_rows, dict) else {}
        albums = album_rows if isinstance(album_rows, dict) else {}
        audio_container = audio_rows if isinstance(audio_rows, dict) else {}
        audio_value = audio_container.get("tracks", audio_container)
        audio = audio_value if isinstance(audio_value, dict) else {}
        lyrics = {
            (norm(row.get("artist")), norm(row.get("track"))): row
            for row in (lyric_rows or []) if isinstance(row, dict)
        }
        album_by_name = {
            (norm(row.get("artist")), norm(row.get("album"))): row
            for row in albums.values()
            if isinstance(row, dict) and row.get("artist") and row.get("album")
        }
        audio_by_name = {
            (norm(row.get("artist")), norm(row.get("track"))): row
            for row in audio.values()
            if isinstance(row, dict) and row.get("artist") and row.get("track")
        }

        artist_records, album_records, songs = {}, {}, {}
        rows = list(track_rows.values()) if isinstance(track_rows, dict) else list(track_rows) if isinstance(track_rows, list) else []
        preferred_artist_ids = {}
        for source_row in rows:
            if isinstance(source_row, dict) and source_row.get("artist"):
                candidate = artist_key(source_row)
                name_key = norm(source_row["artist"])
                current = preferred_artist_ids.get(name_key)
                if current is None or (candidate.startswith("mbid:") and not current.startswith("mbid:")):
                    preferred_artist_ids[name_key] = candidate
        for row in rows:
            if not isinstance(row, dict) or not row.get("artist") or not (row.get("track") or row.get("name")):
                continue
            title = row.get("track") or row.get("name")
            aid = preferred_artist_ids.get(norm(row["artist"])) or artist_key(row)
            bid = album_key(row, aid)
            sid = recording_key(row, aid, bid)
            alias = norm(row["artist"]) + "\0" + norm(title)

            artist_source = artists.get(aid) or artists.get(norm(row["artist"])) or {}
            artist_records.setdefault(aid, {
                "schema_version": 1, "id": aid, "artist": row["artist"],
                "identity": {
                    "artist_mbid": row.get("artist_mbid") or (row.get("artist_id") if aid.startswith("mbid:") else None),
                    "identity_quality": "verified" if aid.startswith("mbid:") else "name_fallback",
                },
                "evidence": artist_source, "album_ids": [],
            })

            album_name = row.get("album") or row.get("album_name") or ""
            if bid:
                album_source = album_by_name.get((norm(row["artist"]), norm(album_name)), {})
                album_records.setdefault(bid, {
                    "schema_version": 1, "id": bid, "artist_id": aid,
                    "artist": row["artist"], "album": album_name,
                    "identity": {
                        "album_mbid": row.get("album_mbid") or row.get("release_mbid"),
                        "identity_quality": "verified" if bid.startswith("mbid:") else "contextual_fallback",
                    },
                    "evidence": album_source, "song_ids": [],
                })
                if bid not in artist_records[aid]["album_ids"]:
                    artist_records[aid]["album_ids"].append(bid)
                if sid not in album_records[bid]["song_ids"]:
                    album_records[bid]["song_ids"].append(sid)

            song = songs.setdefault(sid, {
                "schema_version": 1, "id": sid,
                "identity": {
                    "artist": row["artist"], "title": title, "album": album_name,
                    "artist_id": aid, "album_id": bid,
                    "recording_mbid": row.get("track_mbid") or row.get("recording_mbid"),
                    "spotify_id": row.get("spotify_id") or row.get("spotify_track_id"),
                    "source_track_id": row.get("track_id"),
                    "identity_quality": "verified_recording" if sid.startswith("mbid:")
                        else "spotify_track" if sid.startswith("spotify:")
                        else "source_track_id" if sid.startswith("source:")
                        else "fallback_release_context" if bid else "fallback_artist_title",
                },
                "evidence": {"track_metadata": {}, "audio": {}, "lyrics": None},
                "derived": row.get("derived") or {}, "coverage": row.get("coverage") or {},
                "sources": {}, "relations": {"artist_path": str(self.path_for("artists", aid).relative_to(self.root))},
            })
            if bid:
                song["relations"]["album_path"] = str(self.path_for("albums", bid).relative_to(self.root))

            # Duplicate source rows can refer to the same MBID. Preserve non-empty
            # evidence instead of allowing an empty duplicate to erase a populated row.
            canonical = song["identity"]
            if norm(canonical["artist"]) != norm(row["artist"]) or norm(canonical["title"]) != norm(title):
                variant = {"artist": row["artist"], "title": title, "source_track_id": row.get("track_id")}
                aliases = canonical.setdefault("aliases", [])
                if variant not in aliases:
                    aliases.append(variant)
            for field, value in row.items():
                if field in {"artist", "track", "name", "album", "album_name", "derived", "coverage", "listening_context"}:
                    continue
                if value not in (None, "", [], {}):
                    song["evidence"]["track_metadata"][field] = value
            if row.get("listening_context"):
                song.setdefault("listening_context", {}).update(row["listening_context"])
            if row.get("derived"):
                song["derived"].update(row["derived"])
            if row.get("coverage"):
                song["coverage"].update(row["coverage"])
            audio_row = audio.get(sid) or audio_by_name.get((norm(row["artist"]), norm(title)))
            if audio_row:
                song["evidence"]["audio"] = audio_row
            lyric = lyrics.get((norm(row["artist"]), norm(title)))
            if lyric:
                song["evidence"]["lyrics"] = lyric
            for source_key, status in row.items():
                if not source_key.endswith("_status") or not isinstance(status, str):
                    continue
                old_status = song["sources"].get(source_key, {}).get("status")
                if old_status != "matched" or status == "matched":
                    song["sources"][source_key] = {"status": status}

        index = {
            "schema_version": 1, "songs": {}, "spotify_ids": {},
            "recording_mbids": {}, "name_candidates": {}, "artists": {}, "albums": {},
        }
        for aid, record in artist_records.items():
            path = self.path_for("artists", aid)
            write_json(path, record)
            index["artists"][aid] = {"path": str(path.relative_to(self.root)), "name": record["artist"]}
        for bid, record in album_records.items():
            path = self.path_for("albums", bid)
            write_json(path, record)
            index["albums"][bid] = {"path": str(path.relative_to(self.root)), "artist_id": record["artist_id"], "album": record["album"]}
        for sid, song in songs.items():
            path = self.path_for("songs", sid)
            write_json(path, song)
            identity = song["identity"]
            index["songs"][sid] = {
                "path": str(path.relative_to(self.root)), "artist": identity["artist"],
                "track": identity["title"], "album": identity["album"],
            }
            spotify_id = identity.get("spotify_id")
            if spotify_id:
                index["spotify_ids"][str(spotify_id).rsplit(":", 1)[-1].casefold()] = sid
            mbid = identity.get("recording_mbid")
            if mbid:
                index["recording_mbids"][str(mbid).casefold()] = sid
            index["name_candidates"].setdefault(
                norm(identity["artist"]) + "\0" + norm(identity["title"]), []
            ).append(sid)
        write_json(self.index_path, index)
        self.index = index
        return {
            "artists": len(artist_records), "albums": len(album_records),
            "songs": len(songs),
            "ambiguous_name_aliases": sum(len(values) > 1 for values in index["name_candidates"].values()),
        }


# FILE OVERVIEW
# - Stores one JSON record per artist, album, and song in ID-sharded paths.
# - Uses verified artist/release/recording MBIDs or Spotify IDs before safe aliases.
# - Does not invent album records when the source has no release context.
# - Preserves metadata, listening context, audio, lyrics, derived fields, and provenance.
# - Keeps ambiguous artist/title aliases as candidate lists; never guesses a song version.
