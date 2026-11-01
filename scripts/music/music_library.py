#!/usr/bin/env python3
"""Canonical per-recording music library with lazy reads and stable identity aliases."""
import hashlib
import json
import re
from pathlib import Path

DEFAULT_ROOT = Path("assistant_data/music/music_library")
INDEX_NAME = "library_index.json"

def norm(value):
    return re.sub(r"\\s+", " ", str(value or "").strip()).casefold()

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
    mbid = str(row.get("artist_mbid") or "").strip().casefold()
    return "mbid:" + mbid if mbid else "name:" + digest(norm(row.get("artist")))

def album_key(row, aid):
    mbid = str(row.get("album_mbid") or row.get("release_mbid") or "").strip().casefold()
    return "mbid:" + mbid if mbid else "album:" + digest(aid + "\\0" + norm(row.get("album") or row.get("album_name")))

def recording_key(row, aid, bid):
    mbid = str(row.get("track_mbid") or row.get("recording_mbid") or "").strip().casefold()
    if mbid:
        return "mbid:" + mbid
    sid = str(row.get("spotify_id") or row.get("spotify_track_id") or "").strip()
    if sid.startswith("spotify:track:"):
        sid = sid.rsplit(":", 1)[-1]
    if sid:
        return "spotify:" + sid.casefold()
    duration = row.get("duration_ms") or row.get("duration") or ""
    return "fallback:" + digest(aid + "\\0" + bid + "\\0" + norm(row.get("track") or row.get("name")) + "\\0" + str(duration))

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\\n", encoding="utf-8")
    tmp.replace(path)

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None

class MusicLibrary:
    """Index-backed lazy resolver; recording JSON remains the canonical evidence."""
    def __init__(self, root=DEFAULT_ROOT):
        self.root = Path(root)
        self.index_path = self.root / INDEX_NAME
        self.index = read_json(self.index_path) or {"schema_version": 1, "recordings": {}, "spotify_ids": {}, "recording_mbids": {}, "name_candidates": {}, "artists": {}, "albums": {}}

    def path_for(self, kind, key):
        safe = safe_id(key)
        filename = {"artists": "artist.json", "albums": "album.json", "recordings": "recording.json"}[kind]
        return self.root / kind / safe[:2] / safe / filename

    def get_recording(self, spotify_id=None, recording_mbid=None, artist=None, track=None, album=None):
        key = None
        if spotify_id:
            key = self.index.get("spotify_ids", {}).get(str(spotify_id).rsplit(":", 1)[-1].casefold())
        if key is None and recording_mbid:
            key = self.index.get("recording_mbids", {}).get(str(recording_mbid).casefold())
        if key is None and artist and track:
            candidates = self.index.get("name_candidates", {}).get(norm(artist) + "\\0" + norm(track), [])
            if len(candidates) == 1:
                key = candidates[0]
            elif album:
                matches = [x for x in candidates if norm(self.index["recordings"].get(x, {}).get("album")) == norm(album)]
                if len(matches) == 1:
                    key = matches[0]
        if key is None or key not in self.index.get("recordings", {}):
            return None
        record = read_json(self.root / self.index["recordings"][key]["path"])
        if not isinstance(record, dict):
            return None
        relations = record.get("relations", {})
        artist_record = read_json(self.root / relations.get("artist_path", ""))
        album_record = read_json(self.root / relations.get("album_path", ""))
        return {"recording": record, "artist": artist_record or {}, "album": album_record or {}}

    def put_catalogue(self, track_rows, artist_rows=None, album_rows=None, audio_rows=None, lyric_rows=None):
        artists = artist_rows if isinstance(artist_rows, dict) else {}
        albums = album_rows if isinstance(album_rows, dict) else {}
        audio = audio_rows if isinstance(audio_rows, dict) else {}
        lyrics = {(norm(r.get("artist")), norm(r.get("track"))): r for r in (lyric_rows or []) if isinstance(r, dict)}
        artist_records, album_records, recordings = {}, {}, {}
        for row in track_rows.values() if isinstance(track_rows, dict) else []:
            if not isinstance(row, dict) or not row.get("artist") or not row.get("track"):
                continue
            aid = artist_key(row)
            bid = album_key(row, aid)
            rid = recording_key(row, aid, bid)
            name_key = norm(row["artist"]) + "\\0" + norm(row["track"])
            artist_source = artists.get(aid) or artists.get(norm(row["artist"])) or {}
            album_source = albums.get((norm(row["artist"]), norm(row.get("album") or row.get("album_name"))), {})
            artist_records.setdefault(aid, {"schema_version": 1, "id": aid, "artist": row["artist"], "identity": {"artist_mbid": row.get("artist_mbid"), "identity_quality": "verified" if aid.startswith("mbid:") else "name_fallback"}, "evidence": artist_source, "album_ids": []})
            artist_records[aid]["album_ids"] = sorted(set(artist_records[aid]["album_ids"] + [bid]))
            album_records.setdefault(bid, {"schema_version": 1, "id": bid, "artist_id": aid, "artist": row["artist"], "album": row.get("album") or row.get("album_name") or "", "identity": {"album_mbid": row.get("album_mbid") or row.get("release_mbid"), "identity_quality": "verified" if bid.startswith("mbid:") else "contextual_fallback"}, "evidence": album_source if isinstance(album_source, dict) else {}, "recording_ids": []})
            album_records[bid]["recording_ids"] = sorted(set(album_records[bid]["recording_ids"] + [rid]))
            rec = recordings.setdefault(rid, {"schema_version": 1, "id": rid, "identity": {"artist": row["artist"], "title": row["track"], "album": row.get("album") or row.get("album_name") or "", "artist_id": aid, "album_id": bid, "recording_mbid": row.get("track_mbid") or row.get("recording_mbid"), "spotify_id": row.get("spotify_id") or row.get("spotify_track_id"), "identity_quality": "verified_recording" if rid.startswith("mbid:") else "spotify_track" if rid.startswith("spotify:") else "fallback_release_context"}, "evidence": {"track_metadata": {}, "audio": {}, "lyrics": None}, "derived": row.get("derived") or {}, "coverage": row.get("coverage") or {}, "sources": {}, "relations": {}})
            for field, value in row.items():
                if field not in {"artist", "track", "album", "album_name", "derived", "coverage"}:
                    rec["evidence"]["track_metadata"][field] = value
            rec["evidence"]["audio"] = audio.get(rid) or audio.get(name_key) or {}
            rec["evidence"]["lyrics"] = lyrics.get((norm(row["artist"]), norm(row["track"])))
            rec["sources"] = {k: {"status": v} for k, v in row.items() if k.endswith("_status") and isinstance(v, str)}
            rec["relations"] = {"artist_path": str(self.path_for("artists", aid).relative_to(self.root)), "album_path": str(self.path_for("albums", bid).relative_to(self.root))}
        index = {"schema_version": 1, "recordings": {}, "spotify_ids": {}, "recording_mbids": {}, "name_candidates": {}, "artists": {}, "albums": {}}
        for aid, rec in artist_records.items():
            path = self.path_for("artists", aid); write_json(path, rec)
            index["artists"][aid] = {"path": str(path.relative_to(self.root)), "name": rec["artist"]}
        for bid, rec in album_records.items():
            path = self.path_for("albums", bid); write_json(path, rec)
            index["albums"][bid] = {"path": str(path.relative_to(self.root)), "artist_id": rec["artist_id"], "album": rec["album"]}
        for rid, rec in recordings.items():
            path = self.path_for("recordings", rid); write_json(path, rec)
            ident = rec["identity"]
            index["recordings"][rid] = {"path": str(path.relative_to(self.root)), "artist": ident["artist"], "track": ident["title"], "album": ident["album"]}
            sid = ident.get("spotify_id")
            if sid: index["spotify_ids"][str(sid).rsplit(":", 1)[-1].casefold()] = rid
            mbid = ident.get("recording_mbid")
            if mbid: index["recording_mbids"][str(mbid).casefold()] = rid
            index["name_candidates"].setdefault(norm(ident["artist"]) + "\\0" + norm(ident["title"]), []).append(rid)
        write_json(self.index_path, index)
        self.index = index
        return {"artists": len(artist_records), "albums": len(album_records), "recordings": len(recordings), "ambiguous_name_aliases": sum(len(v) > 1 for v in index["name_candidates"].values())}

# File overview
# - Stores one JSON record per artist, album, and recording in ID-sharded paths.
# - Resolves Spotify track IDs and verified recording MBIDs before safe name aliases.
# - Preserves provider evidence, derived fields, coverage, source statuses, and relations.
# - Keeps ambiguous artist/title aliases as candidate lists; never guesses a version.
