#!/usr/bin/env python3
"""Canonical song library with lazy reads and stable identity aliases."""
import hashlib
import json
import re
from pathlib import Path

# Make package imports work when launched from a script or compatibility entry point.
import sys
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

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



def select_recent_track_rows(track_rows, recent_rows, limit, window_days=None):
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
            "window_days": window_days,
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
            "recording_mbids": {}, "isrcs": {}, "source_track_ids": {}, "name_candidates": {}, "artists": {}, "albums": {},
        }
        # Recover an empty or truncated index from canonical records. This is
        # deliberately a one-time fallback: a populated index keeps lazy reads.
        if not self.index.get("songs") and self.root.exists():
            self._rebuild_index_from_records()

    def _rebuild_index_from_records(self):
        """Recreate lookup aliases from canonical JSON records without provider calls."""
        index = {
            "schema_version": 1, "songs": {}, "spotify_ids": {},
            "recording_mbids": {}, "isrcs": {}, "source_track_ids": {},
            "name_candidates": {}, "artists": {}, "albums": {},
        }
        for path in sorted((self.root / "artists").glob("**/artist.json")):
            record = read_json(path)
            if not isinstance(record, dict) or not record.get("id") or not record.get("artist"):
                continue
            key = record["id"]
            index["artists"][key] = {
                "path": str(path.relative_to(self.root)), "name": record["artist"]
            }
        for path in sorted((self.root / "albums").glob("**/album.json")):
            record = read_json(path)
            if not isinstance(record, dict) or not record.get("id"):
                continue
            key = record["id"]
            index["albums"][key] = {
                "path": str(path.relative_to(self.root)),
                "artist_id": record.get("artist_id") or record.get("identity", {}).get("artist_id"),
                "artist": record.get("artist") or record.get("identity", {}).get("artist"),
                "album": record.get("album") or record.get("identity", {}).get("album"),
            }
        for path in sorted((self.root / "songs").glob("**/song.json")):
            record = read_json(path)
            if not isinstance(record, dict) or not record.get("id"):
                continue
            key = record["id"]
            identity = record.get("identity") or {}
            artist, title = identity.get("artist"), identity.get("title")
            index["songs"][key] = {
                "path": str(path.relative_to(self.root)), "artist": artist, "track": title,
                "album": identity.get("album"), "album_id": identity.get("album_id"),
                "track_number": identity.get("track_number"), "disc_number": identity.get("disc_number"),
            }
            spotify_id = identity.get("spotify_id")
            if spotify_id:
                index["spotify_ids"][str(spotify_id).rsplit(":", 1)[-1].casefold()] = key
            mbid = identity.get("recording_mbid")
            if mbid:
                value = str(mbid).casefold()
                index["recording_mbids"][value] = key
                index["recording_mbids"][value[5:] if value.startswith("mbid:") else "mbid:" + value] = key
            isrc = re.sub(r"[^A-Z0-9]", "", str(identity.get("isrc") or "").upper())
            if isrc:
                index["isrcs"][isrc] = key
            source_id = str(identity.get("source_track_id") or "").casefold()
            if source_id:
                index["source_track_ids"][source_id] = key
            if artist and title:
                index["name_candidates"].setdefault(norm(artist) + "\\0" + norm(title), []).append(key)
        if index["songs"] or index["albums"] or index["artists"]:
            self.root.mkdir(parents=True, exist_ok=True)
            write_json(self.index_path, index)
            self.index = index

    def path_for(self, kind, key):
        safe = safe_id(key)
        filename = {"artists": "artist.json", "albums": "album.json", "songs": "song.json"}[kind]
        return self.root / kind / safe[:2] / safe / filename

    def lookup_song(self, spotify_id=None, recording_mbid=None, isrc=None, source_track_id=None,
                    release_mbid=None, track_number=None, disc_number=None, artist=None, track=None, album=None):
        """Resolve a song and explain the exact identity evidence used."""
        entries = self.index.get("songs", self.index.get("recordings", {}))
        key, matched_by, candidates = None, None, []
        if spotify_id:
            key = self.index.get("spotify_ids", {}).get(str(spotify_id).rsplit(":", 1)[-1].casefold())
            if key: matched_by = "spotify_track_id"
        if key is None and recording_mbid:
            value = str(recording_mbid).casefold()
            aliases = self.index.get("recording_mbids", {})
            key = aliases.get(value) or aliases.get(value[5:] if value.startswith("mbid:") else "mbid:" + value)
            if key: matched_by = "musicbrainz_recording_mbid"
        if key is None and isrc:
            key = self.index.get("isrcs", {}).get(re.sub(r"[^A-Z0-9]", "", str(isrc).upper()))
            if key: matched_by = "isrc"
        if key is None and source_track_id:
            key = self.index.get("source_track_ids", {}).get(str(source_track_id).casefold())
            if key: matched_by = "source_track_id"
        if key is None and release_mbid and track_number is not None:
            release_key = str(release_mbid).casefold()
            if not release_key.startswith("mbid:"): release_key = "mbid:" + release_key
            try:
                wanted_track, wanted_disc = int(track_number), int(disc_number or 1)
                candidates = [song_id for song_id, entry in entries.items()
                    if str((entry or {}).get("album_id") or "").casefold() == release_key
                    and int((entry or {}).get("disc_number") or 1) == wanted_disc
                    and int((entry or {}).get("track_number") or 0) == wanted_track]
            except (TypeError, ValueError):
                candidates = []
            if len(candidates) == 1: key, matched_by = candidates[0], "verified_release_track_position"
        if key is None and artist and track:
            alias = norm(artist) + "\0" + norm(track)
            candidates = self.index.get("name_candidates", {}).get(alias)
            if candidates is None:
                candidates = self.index.get("name_candidates", {}).get(norm(artist) + "\\\\0" + norm(track), [])
            if len(candidates) == 1: key, matched_by = candidates[0], "unique_exact_artist_title"
            elif album:
                matches = [x for x in candidates if norm(entries.get(x, {}).get("album")) == norm(album)]
                if len(matches) == 1: key, matched_by, candidates = matches[0], "exact_artist_title_album", matches
        if key is None:
            ambiguous = bool(candidates and len(candidates) > 1)
            return {"status": "ambiguous" if ambiguous else "not_found", "song_id": None,
                "matched_by": None, "confidence": "unknown", "candidate_ids": list(candidates or []),
                "reason": "multiple exact-name candidates remain" if ambiguous else "no exact indexed identity matched"}
        record = read_json(self.root / entries[key]["path"])
        if not isinstance(record, dict):
            return {"status": "record_missing", "song_id": key, "matched_by": matched_by,
                "confidence": "unknown", "candidate_ids": [key], "reason": "index matched but canonical song file is missing or invalid"}
        from scripts.music.music_evidence import identity_confidence
        confidence = identity_confidence(matched_by, record.get("identity") or {})
        return {"status": "matched", "song_id": key, "matched_by": matched_by,
            "confidence": confidence, "metadata_confidence": (record.get("confidence") or {}).get("metadata", {}),
            "candidate_ids": [key], "reason": "resolved by " + matched_by.replace("_", " "), "record": record}

    def get_song(self, spotify_id=None, recording_mbid=None, artist=None, track=None, album=None,
                 isrc=None, source_track_id=None, release_mbid=None, track_number=None, disc_number=None):
        """Return a song bundle with an inspectable lookup explanation."""
        audit = self.lookup_song(spotify_id=spotify_id, recording_mbid=recording_mbid,
            isrc=isrc, source_track_id=source_track_id, release_mbid=release_mbid,
            track_number=track_number, disc_number=disc_number, artist=artist, track=track, album=album)
        if audit["status"] != "matched": return None
        record = audit["record"]
        relations = record.get("relations", {})
        artist_record = read_json(self.root / relations["artist_path"]) if relations.get("artist_path") else None
        album_record = read_json(self.root / relations["album_path"]) if relations.get("album_path") else None
        return {"song": record, "artist": artist_record or {}, "album": album_record or {},
            "lookup_audit": {key: value for key, value in audit.items() if key != "record"}}

    def get_album(self, album_mbid=None, artist=None, album=None):
        """Resolve an album by release MBID or a unique exact artist/title pair."""
        albums = self.index.get("albums", {})
        key = None
        if album_mbid:
            value = str(album_mbid).casefold()
            key = value if value.startswith("mbid:") else "mbid:" + value
            if key not in albums: key = None
        if key is None and artist and album:
            matches = [album_id for album_id, entry in albums.items()
                if norm(entry.get("artist")) == norm(artist) and norm(entry.get("album")) == norm(album)]
            if len(matches) == 1: key = matches[0]
        return read_json(self.root / albums[key]["path"]) if key else None
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
        for alias_map_name in ("spotify_ids", "recording_mbids", "isrcs", "source_track_ids"):
            for alias, song_id in self.index.get(alias_map_name, {}).items():
                if song_id not in songs:
                    errors.append(f"{alias_map_name} alias references missing song: {alias}")
        return {
            "ok": not errors, "errors": errors,
            "songs": len(songs), "artists": len(artists), "albums": len(albums),
        }

    def put_catalogue(self, track_rows, artist_rows=None, album_rows=None, audio_rows=None, lyric_rows=None):
        try:
            from .music_evidence import (
                album_metadata_confidence, identity_confidence, track_metadata_confidence,
            )
        except ImportError:
            # Compatibility launcher imports this module as top-level music_library.
            from music_evidence import (
                album_metadata_confidence, identity_confidence, track_metadata_confidence,
            )
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

        # Snapshot the current catalogue before rebuilding. Existing records may
        # contain mood assessments, listening context, and evidence absent from
        # the incoming source exports; never discard that accumulated knowledge.
        previous_index = self.index if isinstance(self.index, dict) else {}
        previous_songs = {}
        previous_artists = {}
        previous_albums = {}
        for collection, target in (
            ("songs", previous_songs), ("artists", previous_artists), ("albums", previous_albums)
        ):
            for record_id, entry in (previous_index.get(collection) or {}).items():
                if isinstance(entry, dict) and entry.get("path"):
                    record = read_json(self.root / entry["path"])
                    if isinstance(record, dict):
                        target[record_id] = record

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
                if not album_source.get("identity_verified"):
                    album_source = {}
                album_records.setdefault(bid, {
                    "schema_version": 1, "id": bid, "artist_id": aid,
                    "artist": row["artist"], "album": album_name,
                    "identity": {
                        "album_mbid": row.get("album_mbid") or row.get("release_mbid"),
                        "identity_quality": "verified" if bid.startswith("mbid:") else "contextual_fallback",
                    },
                    "evidence": album_source, "confidence": album_metadata_confidence(album_source), "song_ids": [],
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
                    "isrc": row.get("isrc") or row.get("isrc_code"),
                    "track_number": row.get("track_number") or row.get("position"),
                    "disc_number": row.get("disc_number") or row.get("disc"),
                    "identity_quality": "verified_recording" if sid.startswith("mbid:")
                        else "spotify_track" if sid.startswith("spotify:")
                        else "source_track_id" if sid.startswith("source:")
                        else "fallback_release_context" if bid else "fallback_artist_title",
                },
                "evidence": {"track_metadata": {}, "audio": {}, "lyrics": None},
                "mood": {
                    "status": "not_assessed",
                    "recording_level": {"moods": [], "confidence": "none", "evidence_refs": [], "method": None},
                    "album_context": {"moods": [], "confidence": "none", "evidence_refs": []},
                    "artist_context": {"moods": [], "confidence": "none", "evidence_refs": []},
                    "last_assessed_at": None,
                },
                "confidence": {"identity": identity_confidence(
                    "musicbrainz_recording_mbid" if sid.startswith("mbid:") else
                    "spotify_track_id" if sid.startswith("spotify:") else
                    "source_track_id" if sid.startswith("source:") else "fallback_identity",
                    {"identity_quality": "fallback_artist_title" if sid.startswith("fallback:") else ""}),
                    "metadata": {}},
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
            song["confidence"]["metadata"] = track_metadata_confidence(song["evidence"]["track_metadata"])
            for source_key, status in row.items():
                if not source_key.endswith("_status") or not isinstance(status, str):
                    continue
                old_status = song["sources"].get(source_key, {}).get("status")
                if old_status != "matched" or status == "matched":
                    song["sources"][source_key] = {"status": status}

        # Merge old artist and album records, retaining their evidence and
        # relationships when the current source exports are incomplete.
        for aid, old_record in previous_artists.items():
            if aid not in artist_records:
                artist_records[aid] = old_record
            else:
                current = artist_records[aid]
                current["evidence"] = {**(old_record.get("evidence") or {}), **(current.get("evidence") or {})}
                current["album_ids"] = list(dict.fromkeys(
                    list(old_record.get("album_ids") or []) + list(current.get("album_ids") or [])
                ))
                if old_record.get("identity"):
                    current["identity"] = {
                        **old_record["identity"],
                        **{key: value for key, value in (current.get("identity") or {}).items()
                           if value not in (None, "", [], {})},
                    }
        for bid, old_record in previous_albums.items():
            if bid not in album_records:
                album_records[bid] = old_record
            else:
                current = album_records[bid]
                current["evidence"] = {**(old_record.get("evidence") or {}), **(current.get("evidence") or {})}
                current["song_ids"] = list(dict.fromkeys(
                    list(old_record.get("song_ids") or []) + list(current.get("song_ids") or [])
                ))
                current["confidence"] = {**(old_record.get("confidence") or {}), **(current.get("confidence") or {})}
                if old_record.get("identity"):
                    current["identity"] = {
                        **old_record["identity"],
                        **{key: value for key, value in (current.get("identity") or {}).items()
                           if value not in (None, "", [], {})},
                    }

        # Preserve old songs absent from the incoming rows, and retain their
        # accumulated evidence/mood state when the same stable ID is refreshed.
        for sid, old_record in previous_songs.items():
            if sid not in songs:
                songs[sid] = old_record
                continue
            current = songs[sid]
            old_identity = old_record.get("identity") or {}
            current_identity = current.get("identity") or {}
            current["identity"] = {
                **old_identity,
                **{key: value for key, value in current_identity.items() if value not in (None, "", [], {})},
            }
            # A weaker contextual ID must not replace an established MBID.
            for identity_field in ("artist_id", "album_id"):
                old_value = str(old_identity.get(identity_field) or "")
                new_value = str(current_identity.get(identity_field) or "")
                if old_value.startswith("mbid:") and new_value and not new_value.startswith("mbid:"):
                    current["identity"][identity_field] = old_value
            canonical_artist_id = current["identity"].get("artist_id")
            canonical_album_id = current["identity"].get("album_id")
            current["relations"] = dict(current.get("relations") or {})
            if canonical_artist_id:
                current["relations"]["artist_path"] = str(
                    self.path_for("artists", canonical_artist_id).relative_to(self.root)
                )
            if canonical_album_id:
                current["relations"]["album_path"] = str(
                    self.path_for("albums", canonical_album_id).relative_to(self.root)
                )
            else:
                current["relations"].pop("album_path", None)
            old_evidence = old_record.get("evidence") or {}
            new_evidence = current.get("evidence") or {}
            merged_evidence = dict(old_evidence)
            for evidence_key, evidence_value in new_evidence.items():
                if evidence_value not in (None, "", [], {}):
                    if isinstance(evidence_value, dict) and isinstance(merged_evidence.get(evidence_key), dict):
                        merged_evidence[evidence_key] = {**merged_evidence[evidence_key], **evidence_value}
                    else:
                        merged_evidence[evidence_key] = evidence_value
            current["evidence"] = merged_evidence
            current["mood"] = old_record.get("mood") or current.get("mood") or {}
            current["listening_context"] = {
                **(old_record.get("listening_context") or {}),
                **(current.get("listening_context") or {}),
            }
            current["sources"] = {
                **(old_record.get("sources") or {}),
                **(current.get("sources") or {}),
            }
            for field in ("derived", "coverage"):
                current[field] = {
                    **(old_record.get(field) or {}),
                    **(current.get(field) or {}),
                }
            current["confidence"] = {
                **(old_record.get("confidence") or {}),
                **(current.get("confidence") or {}),
            }

        index = {
            "schema_version": 1, "songs": {}, "spotify_ids": {},
            "recording_mbids": {}, "isrcs": {}, "source_track_ids": {}, "name_candidates": {}, "artists": {}, "albums": {},
        }
        for aid, record in artist_records.items():
            path = self.path_for("artists", aid)
            write_json(path, record)
            index["artists"][aid] = {"path": str(path.relative_to(self.root)), "name": record["artist"]}
        for bid, record in album_records.items():
            path = self.path_for("albums", bid)
            write_json(path, record)
            index["albums"][bid] = {"path": str(path.relative_to(self.root)), "artist_id": record["artist_id"], "artist": record["artist"], "album": record["album"]}
        for sid, song in songs.items():
            path = self.path_for("songs", sid)
            write_json(path, song)
            identity = song["identity"]
            index["songs"][sid] = {
                "path": str(path.relative_to(self.root)), "artist": identity["artist"],
                "track": identity["title"], "album": identity["album"], "album_id": identity.get("album_id"),
                "track_number": identity.get("track_number"), "disc_number": identity.get("disc_number"),
            }
            spotify_id = identity.get("spotify_id")
            if spotify_id:
                index["spotify_ids"][str(spotify_id).rsplit(":", 1)[-1].casefold()] = sid
            mbid = identity.get("recording_mbid")
            if mbid:
                mbid_alias = str(mbid).casefold()
                index["recording_mbids"][mbid_alias] = sid
                index["recording_mbids"][mbid_alias[5:] if mbid_alias.startswith("mbid:") else "mbid:" + mbid_alias] = sid
            isrc = re.sub(r"[^A-Z0-9]", "", str(identity.get("isrc") or "").upper())
            if isrc:
                index["isrcs"][isrc] = sid
            source_id = str(identity.get("source_track_id") or "").casefold()
            if source_id:
                index["source_track_ids"][source_id] = sid
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
# - Uses MusicBrainz/Spotify IDs, ISRCs and verified release positions before safe name aliases.
# - Explains lookup paths and confidence; ambiguous artist/title candidates are never guessed.
# - Does not invent album records when the source has no release context.
# - Preserves metadata, listening context, audio, lyrics, derived fields, and provenance.
