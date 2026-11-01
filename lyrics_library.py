#!/usr/bin/env python3
"""SHIT lyrics lookup and local song-reference library.

Lyrics are fetched transiently for analysis. The local SQLite database stores
song metadata, source references, theme evidence, and one-way phrase fingerprints
rather than copying full copyrighted lyric text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "data" / "lyrics" / "library.sqlite3"
APP_UA = "SHIT-Lyrics-Library/1.0 (https://github.com/TrickySturluson/tricky-lastfm)"
THEMES = {
    "horror": {"horror", "terror", "nightmare", "fear", "scream", "haunt", "haunted", "spooky"},
    "murder_slasher": {"murder", "killer", "kill", "slaughter", "stab", "knife", "chainsaw", "blood"},
    "monster": {"monster", "creature", "beast", "demon", "devil", "werewolf", "frankenstein"},
    "vampire": {"vampire", "dracula", "fang", "bloodsucker", "undead"},
    "zombie_undead": {"zombie", "undead", "grave", "cemetery", "corpse", "resurrection", "dead"},
    "ghost_supernatural": {"ghost", "spirit", "witch", "witches", "curse", "voodoo", "possess"},
    "halloween_party": {"halloween", "costume", "trick", "treat", "pumpkin", "monster", "midnight"},
    "occult": {"satan", "satanic", "occult", "ritual", "hex", "spell", "hell"},
}
TOKEN_RE = re.compile(r"[a-z0-9']+")


def now():
    return datetime.now(timezone.utc).isoformat()


def normalize(text):
    return " ".join(TOKEN_RE.findall((text or "").casefold()))


def request_json(url, headers=None, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": APP_UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 401, 403):
            return None
        if exc.code == 429:
            raise RuntimeError(f"Provider rate limited the request; retry after {exc.headers.get('Retry-After', 'a short wait')}.") from exc
        raise RuntimeError(f"Lyrics provider returned HTTP {exc.code}.") from exc
    except (TimeoutError, urllib.error.URLError) as exc:
        raise RuntimeError(f"Lyrics provider unavailable: {exc}") from exc


def lrclib_lookup(title, artist, album=None, duration=None):
    params = {"track_name": title, "artist_name": artist}
    if album:
        params["album_name"] = album
    if duration:
        params["duration"] = str(int(duration))
    url = "https://lrclib.net/api/get?" + urllib.parse.urlencode(params)
    item = request_json(url)
    if not item:
        return None
    return {"provider": "lrclib", "provider_id": str(item.get("id", "")),
            "title": item.get("trackName") or title, "artist": item.get("artistName") or artist,
            "album": item.get("albumName") or album, "lyrics": item.get("plainLyrics") or strip_lrc(item.get("syncedLyrics") or ""),
            "instrumental": bool(item.get("instrumental")), "url": f"https://lrclib.net/api/get/{item.get('id')}"}


def strip_lrc(value):
    return re.sub(r"(?m)^\s*\[\d{2}:\d{2}(?:\.\d+)?\]\s*", "", value or "")


def musixmatch_lookup(title, artist):
    key = os.getenv("MUSIXMATCH_API_KEY", "").strip()
    if not key:
        return None
    params = urllib.parse.urlencode({"q_track": title, "q_artist": artist, "apikey": key, "format": "json"})
    data = request_json("https://api.musixmatch.com/ws/1.1/matcher.lyrics.get?" + params)
    body = ((data or {}).get("message") or {}).get("body") or {}
    lyrics = (body.get("lyrics") or {}).get("lyrics_body")
    if not lyrics:
        return None
    track = ((data or {}).get("message") or {}).get("header") or {}
    return {"provider": "musixmatch", "provider_id": str(track.get("status_code", "")),
            "title": title, "artist": artist, "album": None, "lyrics": lyrics,
            "instrumental": False, "url": "https://www.musixmatch.com/"}


def genius_search(title, artist):
    """Genius official API is a metadata/link fallback; it does not expose full lyrics."""
    token = os.getenv("GENIUS_ACCESS_TOKEN", "").strip()
    if not token:
        return None
    query = urllib.parse.urlencode({"q": f"{artist} {title}"})
    data = request_json("https://api.genius.com/search?" + query, {"Authorization": f"Bearer {token}"})
    hits = (((data or {}).get("response") or {}).get("hits") or [])
    for hit in hits:
        result = hit.get("result") or {}
        if result.get("url"):
            return {"provider": "genius", "provider_id": str(result.get("id", "")),
                    "title": result.get("title") or title,
                    "artist": ((result.get("primary_artist") or {}).get("name") or artist),
                    "album": None, "lyrics": "", "instrumental": False,
                    "url": result["url"]}
    return None


def analyze_lyrics(lyrics):
    words = TOKEN_RE.findall((lyrics or "").casefold())
    counts = {}
    for theme, terms in THEMES.items():
        hits = sorted({word for word in words if word in terms})
        if hits:
            counts[theme] = {"count": sum(words.count(word) for word in hits), "evidence_terms": hits}
    total = sum(item["count"] for item in counts.values())
    # Conservative rule: a theme needs multiple distinct indicators or repeated use.
    qualifying = {k: v for k, v in counts.items() if len(v["evidence_terms"]) >= 2 or v["count"] >= 3}
    score = min(1.0, sum(v["count"] for v in qualifying.values()) / max(12, len(words) * 0.08))
    return {"themes": qualifying, "raw_theme_hits": counts, "word_count": len(words),
            "horror_relevance": round(score, 3),
            "assessment": "strong" if score >= .35 else "possible" if score >= .12 else "weak"}


def phrase_fingerprints(lyrics, n=5):
    tokens = TOKEN_RE.findall((lyrics or "").casefold())
    if len(tokens) < n:
        return []
    # Hashes allow phrase matching without retaining reconstructable lyric text.
    return [hashlib.sha256(" ".join(tokens[i:i+n]).encode()).hexdigest()
            for i in range(len(tokens)-n+1)]


class LyricsLibrary:
    def __init__(self, db_path=DEFAULT_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS songs (
          id INTEGER PRIMARY KEY, title TEXT NOT NULL, artist TEXT NOT NULL,
          album TEXT, duration REAL, normalized_title TEXT NOT NULL,
          normalized_artist TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          UNIQUE(normalized_title, normalized_artist)
        );
        CREATE TABLE IF NOT EXISTS sources (
          song_id INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
          provider TEXT NOT NULL, provider_id TEXT, url TEXT, checked_at TEXT NOT NULL,
          has_lyrics INTEGER NOT NULL DEFAULT 0, UNIQUE(song_id, provider)
        );
        CREATE TABLE IF NOT EXISTS analyses (
          song_id INTEGER PRIMARY KEY REFERENCES songs(id) ON DELETE CASCADE,
          themes_json TEXT NOT NULL, relevance REAL NOT NULL, assessment TEXT NOT NULL,
          word_count INTEGER NOT NULL, analyzed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS phrase_hashes (
          song_id INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
          phrase_hash TEXT NOT NULL, UNIQUE(song_id, phrase_hash)
        );
        CREATE INDEX IF NOT EXISTS idx_songs_artist ON songs(normalized_artist);
        CREATE INDEX IF NOT EXISTS idx_phrase_hash ON phrase_hashes(phrase_hash);
        """)
        self.db.commit()

    def close(self):
        self.db.close()

    def save(self, title, artist, album=None, duration=None, results=()):
        stamp = now()
        self.db.execute("""INSERT INTO songs(title,artist,album,duration,normalized_title,normalized_artist,created_at,updated_at)
          VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(normalized_title,normalized_artist) DO UPDATE SET
          title=excluded.title, album=COALESCE(excluded.album,songs.album),
          duration=COALESCE(excluded.duration,songs.duration), updated_at=excluded.updated_at""",
          (title, artist, album, duration, normalize(title), normalize(artist), stamp, stamp))
        row = self.db.execute("SELECT id FROM songs WHERE normalized_title=? AND normalized_artist=?",
                              (normalize(title), normalize(artist))).fetchone()
        sid = row["id"]
        for result in results:
            self.db.execute("""INSERT INTO sources(song_id,provider,provider_id,url,checked_at,has_lyrics)
              VALUES(?,?,?,?,?,?) ON CONFLICT(song_id,provider) DO UPDATE SET
              provider_id=excluded.provider_id,url=excluded.url,checked_at=excluded.checked_at,has_lyrics=excluded.has_lyrics""",
              (sid, result["provider"], result.get("provider_id"), result.get("url"), stamp, int(bool(result.get("lyrics")))))
            lyrics = result.get("lyrics") or ""
            if lyrics:
                analysis = analyze_lyrics(lyrics)
                self.db.execute("""INSERT INTO analyses(song_id,themes_json,relevance,assessment,word_count,analyzed_at)
                  VALUES(?,?,?,?,?,?) ON CONFLICT(song_id) DO UPDATE SET themes_json=excluded.themes_json,
                  relevance=excluded.relevance,assessment=excluded.assessment,word_count=excluded.word_count,analyzed_at=excluded.analyzed_at""",
                  (sid, json.dumps(analysis["themes"], ensure_ascii=False), analysis["horror_relevance"],
                   analysis["assessment"], analysis["word_count"], stamp))
                hashes = phrase_fingerprints(lyrics)
                self.db.executemany("INSERT OR IGNORE INTO phrase_hashes(song_id,phrase_hash) VALUES(?,?)",
                                    [(sid, h) for h in hashes])
        self.db.commit()
        return sid

    def lookup(self, title=None, artist=None, phrase=None, limit=20):
        if phrase:
            hashes = phrase_fingerprints(phrase)
            if not hashes:
                return []
            rows = self.db.execute("""SELECT s.*, a.themes_json,a.relevance,a.assessment,COUNT(DISTINCT p.phrase_hash) matches
              FROM phrase_hashes p JOIN songs s ON s.id=p.song_id
              LEFT JOIN analyses a ON a.song_id=s.id
              WHERE p.phrase_hash IN (%s) GROUP BY s.id ORDER BY matches DESC LIMIT ?""" %
              ",".join("?" for _ in hashes), (*hashes, limit)).fetchall()
        else:
            clauses, args = [], []
            if title:
                clauses.append("normalized_title LIKE ?"); args.append("%"+normalize(title)+"%")
            if artist:
                clauses.append("normalized_artist LIKE ?"); args.append("%"+normalize(artist)+"%")
            if not clauses:
                return self.recent(limit)
            rows = self.db.execute("""SELECT s.*,a.themes_json,a.relevance,a.assessment,0 matches
              FROM songs s LEFT JOIN analyses a ON a.song_id=s.id WHERE """+
              " AND ".join(clauses)+" ORDER BY s.updated_at DESC LIMIT ?", (*args,limit)).fetchall()
        return [dict(r) for r in rows]

    def recent(self, limit=20):
        rows = self.db.execute("""SELECT s.*,a.themes_json,a.relevance,a.assessment,0 matches
          FROM songs s LEFT JOIN analyses a ON a.song_id=s.id ORDER BY s.updated_at DESC LIMIT ?""",(limit,)).fetchall()
        return [dict(r) for r in rows]


def search_and_analyze(title, artist, album=None, duration=None, db_path=DEFAULT_DB):
    providers = (lrclib_lookup, musixmatch_lookup, genius_search)
    results, errors = [], []
    for provider in providers:
        try:
            item = provider(title, artist, album, duration) if provider is lrclib_lookup else provider(title, artist)
            if item:
                results.append(item)
        except Exception as exc:
            errors.append(f"{provider.__name__}: {exc}")
        time.sleep(.25)
    library = LyricsLibrary(db_path)
    try:
        library.save(title, artist, album, duration, results)
        return {"song": {"title": title, "artist": artist, "album": album},
                "sources": [{"provider": r["provider"], "url": r["url"], "lyrics_found": bool(r.get("lyrics"))} for r in results],
                "analysis": analyze_lyrics(next((r["lyrics"] for r in results if r.get("lyrics")), "")),
                "errors": errors, "stored_locally": True}
    finally:
        library.close()


def main():
    parser = argparse.ArgumentParser(description="SHIT lyrics lookup and local song-reference library")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="Fetch lyrics from configured sources and analyze themes")
    analyze.add_argument("title"); analyze.add_argument("artist")
    analyze.add_argument("--album"); analyze.add_argument("--duration", type=float)
    lookup = sub.add_parser("lookup", help="Search the local song library")
    lookup.add_argument("--title"); lookup.add_argument("--artist"); lookup.add_argument("--phrase")
    lookup.add_argument("--limit", type=int, default=20)
    sub.add_parser("recent", help="Show recently indexed songs")
    args = parser.parse_args()
    if args.command == "analyze":
        print(json.dumps(search_and_analyze(args.title,args.artist,args.album,args.duration,args.db),indent=2,ensure_ascii=False))
    else:
        lib = LyricsLibrary(args.db)
        try:
            rows = lib.lookup(args.title,args.artist,args.phrase,args.limit) if args.command == "lookup" else lib.recent()
            print(json.dumps(rows,indent=2,ensure_ascii=False))
        finally:
            lib.close()


if __name__ == "__main__":
    main()
