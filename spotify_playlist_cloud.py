#!/usr/bin/env python3
import time
"""Owner-verified GitHub issue command handler for Spotify playlist control."""
import json
import os
import re
import secrets
import sys
import urllib.error
import urllib.parse
from pathlib import Path

import spotify_playlist_manager as manager
import playlist_intelligence as intelligence

STATE = Path(".github/spotify_playlist_manager_state.json")
OWNER = "TrickySturluson"
CONTROL_ISSUE_TITLE = "Spotify Playlist Manager Control"

DAILY_DESCRIPTIONS = [
    "Could be worse. Could be quiet.",
    "At least the music's good.",
    "Well, something here has decent taste.",
    "Familiar names. Unexpected detours",
    "Not too many hits yesterday, that was then this is an improvement.",
    "The skip button is there for a reason. Hope you don't need it.",
    "The playlist's doing the heavy lifting... again.",
    "I've made a few adjustments. You're welcome.",
    "Today's queue has considerably better judgment.",
    "A little less filler... maybe..",
    "Good music doesn't find itself, try not to miss it.",
    "Trust the queue. It's got a better track record.",
    "Some things are better left on repeat.",
    "A little distortion never hurt anybody.",
    "Nothing groundbreaking. Just breaking the silence.",
    "No encore necessary. I'll be here all day.",
    "Your daily dose of questionable taste.",
    "Today's queue. Don't say I never do anything for you.",
]


def fail(message):
    print(message, file=sys.stderr)
    raise SystemExit(1)


def owned_playlist(sp, pid, me):
    # Do not use /me/playlists for mutation checks: Spotify may return a stale
    # snapshot_id in that collection response after a playlist write. Fetch the
    # playlist resource directly so preview/confirm/undo compare the live version.
    try:
        p = sp.call("GET", f"/playlists/{pid}")
    except manager.ManagerError:
        fail("Rejected: playlist not found or not accessible by this account.")
    if not isinstance(p, dict) or p.get("id") != pid or (p.get("owner") or {}).get("id") != me.get("id"):
        fail("Rejected: playlist not found or not owned by this account.")
    return p


def snapshot_uris(snapshot):
    return [item.get("uri") for item in snapshot.get("items", [])]


def pending_state_matches(playlist, pending, current_snapshot=None):
    # Playlist edits and undo both operate on ordered items. Compare the exact
    # ordered URI list captured at preview instead of Spotify's unreliable
    # snapshot_id across separate workflow runners. Legacy pending previews
    # without expected_uris retain their original snapshot check.
    if "expected_uris" in pending:
        return (
            current_snapshot is not None
            and snapshot_uris(current_snapshot) == pending.get("expected_uris")
        )
    return playlist.get("snapshot_id") == pending.get("snapshot_id")


def completed_state_matches(playlist, completed, current_snapshot):
    # Validate the live playlist against the exact ordered contents recorded
    # immediately after the completed edit. Keep snapshot_id as a legacy fallback.
    if "after_uris" in completed:
        return snapshot_uris(current_snapshot) == completed.get("after_uris")
    return playlist.get("snapshot_id") == completed.get("after_snapshot_id")


def replace_playlist(sp, pid, uris):
    # Replace the first page, then append in order; duplicate URIs are preserved.
    if not manager.unlocked(pid):
        raise manager.ManagerError("Playlist is LOCKED; undo was stopped before restoration.")
    first = uris[:100]
    if first:
        sp.call("PUT", f"/playlists/{pid}/items", {"uris": first})
        for offset in range(100, len(uris), 100):
            if not manager.unlocked(pid):
                raise manager.ManagerError("Playlist locked during undo; remaining restoration stopped.")
            sp.call("POST", f"/playlists/{pid}/items", {"uris": uris[offset:offset + 100]})
    else:
        current = [item.get("uri") for item in manager.tracks(sp, manager.find(sp, pid)) if item.get("uri")]
        if current:
            manager.remove(sp, pid, current)


def cleanup_duplicates(sp, pid):
    """Remove surplus exact track-URI occurrences, preserving the first copy and order."""
    if not manager.unlocked(pid):
        raise manager.ManagerError("Playlist is LOCKED; duplicate cleanup was stopped.")
    playlist = owned_playlist(sp, pid, sp.me())
    current = manager.snapshot(sp, playlist)
    positions = {}
    for index, item in enumerate(current.get("items", [])):
        uri = item.get("uri")
        if isinstance(uri, str) and uri.startswith("spotify:track:"):
            positions.setdefault(uri, []).append(index)
    duplicates = {uri: indexes[1:] for uri, indexes in positions.items() if len(indexes) > 1}
    surplus = sum(len(indexes) for indexes in duplicates.values())
    if not surplus:
        return 0
    # The caller has already saved the pre-edit recovery snapshot. Use Spotify's
    # positional removal API so only surplus copies are removed.
    if not manager.unlocked(pid):
        raise manager.ManagerError("Playlist locked before duplicate removal; cleanup stopped.")
    items = [{"uri": uri, "positions": indexes} for uri, indexes in duplicates.items()]
    sp.call("DELETE", f"/playlists/{pid}/items", {
        "items": items, "snapshot_id": playlist.get("snapshot_id")
    })
    manager.audit(
        event="duplicate_cleanup", playlist_id=pid,
        duplicate_uri_count=len(duplicates), surplus_count=surplus,
    )
    return surplus


def execute(sp, pid, operations):
    for op in operations:
        if not manager.unlocked(pid):
            raise manager.ManagerError("Playlist locked during execution; remaining changes stopped.")
        action = op["action"]
        if action == "add":
            manager.add(sp, pid, op["uris"])
        elif action == "remove":
            manager.remove(sp, pid, op["uris"])
        elif action == "replace":
            current = [x["uri"] for x in manager.tracks(sp, manager.find(sp, pid)) if x.get("uri")]
            if current:
                manager.remove(sp, pid, current)
            manager.add(sp, pid, op["uris"])
        elif action == "reorder":
            current = manager.find(sp, pid)
            sp.call("PUT", f"/playlists/{pid}/items", {
                "range_start": op["range_start"],
                "insert_before": op["insert_before"],
                "range_length": op["range_length"],
                "snapshot_id": current.get("snapshot_id"),
            })
        elif action == "details":
            sp.call("PUT", f"/playlists/{pid}", {
                "name": op["name"],
                "description": op["description"],
            })


def main():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    issue = event.get("issue") or {}
    sender = (event.get("sender") or {}).get("login", "")
    if sender.casefold() != OWNER.casefold():
        fail("Rejected: command sender is not the repository owner.")
    if issue.get("title") != CONTROL_ISSUE_TITLE or issue.get("state") != "open":
        fail("Rejected: this is not the active control issue.")

    try:
        command = json.loads(issue.get("body") or "")
    except json.JSONDecodeError:
        fail("Command body must be a JSON object.")
    if not isinstance(command, dict):
        fail("Rejected: command must be a JSON object.")
    action = command.get("command")
    allowed = {
        "status": {"command"},
        "inspect": {"command", "playlist_id"},
        "cleanup_on": {"command", "playlist_id"},
        "cleanup_off": {"command", "playlist_id"},
        "cleanup_check": {"command", "playlist_id"},
        "cleanup_run": {"command", "playlist_id"},
        "health": {"command", "playlist_id"},
        "lock_all": {"command"},
        "lock": {"command", "playlist_id"},
        "unlock": {"command", "playlist_id"},
        "preview": {"command", "playlist_id", "operations"},
        "daily_preview": {"command", "playlist_id"},
        "horror_preview": {"command", "playlist_id"},
        "booze20_preview": {"command", "playlist_id"},
        "booze20_uri_preview": {"command", "playlist_id", "tracks"},
        "booze20_resolve_sources": {"command", "sources"},
        "confirm": {"command", "confirmation"},
        "undo": {"command"},
    }
    if action not in allowed or set(command) != allowed[action]:
        fail("Rejected: invalid command or fields.")
    if action in {"lock", "unlock", "preview", "daily_preview", "horror_preview", "inspect", "booze20_preview", "booze20_uri_preview", "cleanup_on", "cleanup_off", "cleanup_check", "cleanup_run", "health"} and not isinstance(command.get("playlist_id"), str):
        fail("Rejected: a playlist_id is required.")
    if action == "confirm" and not isinstance(command.get("confirmation"), str):
        fail("Rejected: confirmation code is required.")

    manager.CID = os.environ["SPOTIFY_CLIENT_ID"]
    manager.TOKEN = Path(".spotify_playlist_token.json")
    manager.CONFIG = STATE
    manager.AUDIT = Path(".github/spotify_playlist_manager_audit.jsonl")
    manager.BACKUPS = Path("playlist_backups")
    manager.write(manager.TOKEN, {
        "refresh_token": os.environ["SPOTIFY_REFRESH_TOKEN"],
        "obtained_at": 0,
        "expires_in": 0,
    })
    sp = manager.Spotify()
    config = manager.config()
    manager.write(STATE, config)
    playlists = sp.playlists()
    me = sp.me()
    owned = [p for p in playlists if (p.get("owner") or {}).get("id") == me.get("id")]
    result = ""

    if action == "lock_all":
        for p in owned:
            prior = config["playlists"].get(p["id"], {})
            config["playlists"][p["id"]] = {
                **prior, "name": p.get("name", ""),
                "state": "locked", "updated_at": manager.stamp()
            }
        config.pop("pending", None)
        manager.write(STATE, config)
        manager.audit(event="lock_all", count=len(owned))
        result = f"Locked all {len(owned)} playlists owned by this account."
    elif action in {"cleanup_on", "cleanup_off"}:
        p = owned_playlist(sp, command["playlist_id"], me)
        entry = config["playlists"].setdefault(p["id"], {})
        entry.update({"name": p.get("name", ""), "cleanup": action == "cleanup_on", "updated_at": manager.stamp()})
        manager.write(STATE, config)
        manager.audit(event="cleanup_enabled" if action == "cleanup_on" else "cleanup_disabled", playlist_id=p["id"], name=p.get("name"))
        result = f'Duplicate auto-cleanup is {"ON" if action == "cleanup_on" else "OFF"} for "{p.get("name")}".'
    elif action == "cleanup_run":
        pid = command["playlist_id"]
        p = owned_playlist(sp, pid, me)
        if not manager.unlocked(pid):
            fail("Blocked: playlist is LOCKED. Unlock it explicitly before duplicate cleanup.")
        before = manager.snapshot(sp, p)
        backup = manager.save_snapshot(before)
        removed = cleanup_duplicates(sp, pid)
        updated = owned_playlist(sp, pid, me)
        after = manager.snapshot(sp, updated)
        config["last_completed"] = {
            "playlist_id": pid, "backup": backup,
            "backup_run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "after_snapshot_id": updated.get("snapshot_id"),
            "after_uris": snapshot_uris(after), "kind": "cleanup",
        }
        manager.write(STATE, config)
        manager.audit(event="cleanup_completed", playlist_id=pid, removed_count=removed, backup=backup)
        result = (
            f'Duplicate cleanup complete for "{updated.get("name")}". '
            f'Removed {removed} surplus copy/copies; kept the first occurrence of each track. '
            f'{"No duplicates were found. " if not removed else ""}'
            "A recovery snapshot was saved. Playlist remains UNLOCKED."
        )
    elif action == "health":
        p = owned_playlist(sp, command["playlist_id"], me)
        current = manager.snapshot(sp, p)
        try:
            import spotify_discovery as daily
            feedback = daily.load_playlist_feedback(current["items"], p["id"])
        except Exception:
            feedback = {}
        health = intelligence.playlist_health(current["items"], feedback)
        profile = intelligence.build_playlist_profile(current["items"], feedback)
        lines = [
            f'PLAYLIST HEALTH — {p.get("name")} [{p["id"]}]',
            f'Items: {health["track_count"]}; primary artists: {health["unique_primary_artists"]}; unique track URIs: {health["unique_track_uris"]}.',
            f'Duplicate URI groups: {len(health["duplicate_uri_groups"])}; surplus copies: {health["surplus_duplicates"]}.',
            f'Missing URIs: {health["missing_uri_items"]}; non-track items: {health["non_track_items"]}.',
            f'Top artist share: {health["top_artist_share"]:.0%}; artist metadata coverage: {health["artist_metadata_coverage"]:.0%}.',
            f'Playlist-specific feedback: {health["removal_feedback_count"]} removals; {health["whitelisted_count"]} whitelisted re-additions.',
            "Top artists: " + (", ".join(f'{row["artist"]} ({row["tracks"]})' for row in profile["top_artists"][:5]) or "none"),
            "Genre signals: " + (", ".join(row["tag"] for row in profile["genres"][:8]) or "not enough metadata"),
            "Mood signals: " + (", ".join(row["tag"] for row in profile["moods"][:6]) or "not enough metadata"),
            "Read-only report; no playlist changes were made.",
        ]
        for row in health["duplicate_uri_groups"]:
            lines.append(f'DUPLICATE: {row["uri"]} appears {row["count"]} times ({row["surplus"]} surplus).' )
        result = "\\n".join(lines)
    elif action == "cleanup_check":
        p = owned_playlist(sp, command["playlist_id"], me)
        current = manager.snapshot(sp, p)
        positions = {}
        for index, item in enumerate(current.get("items", [])):
            uri = item.get("uri")
            if isinstance(uri, str) and uri.startswith("spotify:track:"):
                positions.setdefault(uri, []).append(index)
        duplicates = [(uri, indexes) for uri, indexes in positions.items() if len(indexes) > 1]
        surplus = sum(len(indexes) - 1 for _, indexes in duplicates)
        lines = [f'DUPLICATE CHECK — {p.get("name")} [{p["id"]}]', f'Duplicate tracks: {len(duplicates)}; surplus copies: {surplus}.']
        for uri, indexes in duplicates:
            lines.append(f'KEEP position {indexes[0] + 1}; remove {len(indexes) - 1} extra copy/copies: {uri}')
        lines.append("Read-only check; no changes made.")
        result = "\n".join(lines)
    elif action in {"lock", "unlock"}:
        p = owned_playlist(sp, command["playlist_id"], me)
        state = "locked" if action == "lock" else "unlocked"
        prior = config["playlists"].get(p["id"], {})
        config["playlists"][p["id"]] = {
            **prior, "name": p.get("name", ""), "state": state, "updated_at": manager.stamp()
        }
        if state == "locked" and (config.get("pending") or {}).get("playlist_id") == p["id"]:
            config.pop("pending", None)
        manager.write(STATE, config)
        manager.audit(event="permission_changed", playlist_id=p["id"], name=p.get("name"), state=state)
        result = f'{p.get("name")} is now {state.upper()}.'
    elif action == "inspect":
        pid = command["playlist_id"]
        p = owned_playlist(sp, pid, me)
        current = manager.snapshot(sp, p)
        lines = [f'PLAYLIST INSPECTION — {p.get("name")} [{pid}]', f'Items: {len(current["items"])}', "Read-only; no playlist changes have been made.", ""]
        for index, item in enumerate(current["items"], 1):
            artists = ", ".join(item.get("artists") or [])
            lines.append(f'{index:02d}. {artists} — {item.get("name")} [{item.get("uri")}]')
        result = "\n".join(lines)
    elif action == "preview":
        pid, operations = manager.validate({
            "playlist_id": command["playlist_id"], "operations": command["operations"]
        })
        p = owned_playlist(sp, pid, me)
        if not manager.unlocked(pid):
            fail("Blocked: playlist is LOCKED. Unlock it explicitly before previewing edits.")
        preview_snapshot = manager.snapshot(sp, p)
        confirmation = secrets.token_urlsafe(12)
        config["pending"] = {
            "playlist_id": pid,
            "operations": operations,
            "snapshot_id": p.get("snapshot_id"),
            "expected_uris": snapshot_uris(preview_snapshot),
            "confirmation": confirmation,
        }
        manager.write(STATE, config)
        manager.audit(event="change_previewed", playlist_id=pid, operations=operations)
        lines = [f'PREVIEW — {p.get("name")} [{pid}]', "No playlist changes have been made."]
        for op in operations:
            if op["action"] in {"add", "remove", "replace"}:
                lines.append(f'{op["action"].upper()}: {len(op["uris"])} track URI(s)')
                lines.extend("  " + uri for uri in op["uris"])
            elif op["action"] == "details":
                lines.append(f'UPDATE DETAILS: name={op["name"]!r}; description={op["description"]!r}')
            else:
                lines.append(
                    f'REORDER: start {op["range_start"]}, before {op["insert_before"]}, '
                    f'length {op["range_length"]}'
                )
        lines.extend([
            "",
            "To execute this exact preview, submit a confirm command with this code:",
            confirmation,
            "The playlist must remain unlocked and unchanged until confirmation.",
        ])
        result = "\n".join(lines)
    elif action == "booze20_preview":
        # Resolve the user's 20-track dark/playful/chaotic party batch through Spotify's catalogue.
        candidates = [
            ("DJ Jazzy Jeff & The Fresh Prince", "A Nightmare on My Street"),
            ("OutKast", "Dracula's Wedding"),
            ("Whodini", "Freaks Come Out at Night"),
            ("Geto Boys", "Mind Playing Tricks on Me"),
            ("Gnarls Barkley", "The Boogie Monster"),
            ("Nas", "Black Magic"),
            ("The Prodigy", "Voodoo People"),
            ("Yeah Yeah Yeahs", "Heads Will Roll - A-Trak Remix"),
            ("PinkPantheress", "Another Life"),
            ("Strafe", "Set It Off"),
            ("Rihanna", "Disturbia"),
            ("Billie Eilish", "Bury a Friend"),
            ("Lana Del Rey", "Season of the Witch"),
            ("Scissor Sisters", "I Can't Decide"),
            ("Kesha", "Cannibal"),
            ("Shakira", "She Wolf"),
            ("Oingo Boingo", "Dead Man's Party"),
            ("The Specials", "Ghost Town"),
            ("Siouxsie and the Banshees", "Spellbound"),
            ("Godsmack", "Voodoo"),
        ]
        pid = command["playlist_id"]
        p = owned_playlist(sp, pid, me)
        if not manager.unlocked(pid):
            fail("Blocked: playlist is LOCKED. Unlock it explicitly before resolving the 20-track batch.")
        current = manager.snapshot(sp, p)
        existing = {item.get("uri") for item in current["items"] if item.get("uri")}
        def music_key(value):
            return "".join(ch for ch in str(value or "").casefold() if ch.isalnum())
        resolved, skipped, already_present = [], [], []
        def catalog_search(query):
            for attempt in range(3):
                try:
                    return sp.call("GET", "/search?" + query)
                except manager.ManagerError as error:
                    message = str(error)
                    if "QUOTA_EXCEEDED" in message:
                        raise manager.ManagerError(
                            "Spotify catalogue quota is exhausted (QUOTA_EXCEEDED). "
                            "Stopped immediately without retrying; use booze20_uri_preview "
                            "with verified Spotify track URIs instead."
                        ) from error
                    if "HTTP 429" not in message or attempt == 2:
                        raise
                    match = re.search(r"Retry-After:\s*([0-9]+(?:\.[0-9]+)?)", message)
                    if not match:
                        raise manager.ManagerError(
                            "Spotify returned HTTP 429 without Retry-After; stopped rather than guessing."
                        ) from error
                    delay = float(match.group(1))
                    if delay > 120:
                        raise manager.ManagerError(
                            f"Spotify rate limit requires waiting {delay:g}s; stopped this run safely."
                        ) from error
                    time.sleep(delay)
            raise manager.ManagerError("Spotify catalogue retry limit reached.")
        track_cache = config.setdefault("track_uri_cache", {})
        for artist, title in candidates:
            target_artist, target_title = music_key(artist), music_key(title)
            cache_key = target_artist + "|" + target_title
            cached = track_cache.get(cache_key)
            if (
                isinstance(cached, dict)
                and isinstance(cached.get("uri"), str)
                and cached["uri"].startswith("spotify:track:")
                and isinstance(cached.get("name"), str)
            ):
                match = {
                    "name": cached["name"], "uri": cached["uri"],
                    "artists": [{"name": artist}],
                }
            else:
                time.sleep(1.0)
                query = urllib.parse.urlencode({
                    "type": "track", "limit": 10,
                    "q": f'artist:"{artist}" track:"{title}"',
                })
                page = catalog_search(query)
                matches = ((page or {}).get("tracks") or {}).get("items") or []
                match = next((
                    track for track in matches
                    if music_key(track.get("name")) == target_title
                    and any(music_key(a.get("name")) == target_artist for a in (track.get("artists") or []))
                    and isinstance(track.get("uri"), str)
                    and track["uri"].startswith("spotify:track:")
                ), None)
                if not match:
                    fallback_query = urllib.parse.urlencode({
                        "type": "track", "limit": 10, "q": f'track:"{title}"',
                    })
                    fallback_page = catalog_search(fallback_query)
                    fallback_matches = ((fallback_page or {}).get("tracks") or {}).get("items") or []
                    match = next((
                        track for track in fallback_matches
                        if music_key(track.get("name")).startswith(target_title)
                        and any(music_key(a.get("name")) == target_artist for a in (track.get("artists") or []))
                        and isinstance(track.get("uri"), str)
                        and track["uri"].startswith("spotify:track:")
                    ), None)
                if match:
                    track_cache[cache_key] = {"name": match["name"], "uri": match["uri"]}
                    manager.write(STATE, config)
            if not match:
                skipped.append(f"{artist} — {title} (no exact Spotify match)")
                continue
            if match["uri"] in existing:
                already_present.append(f"{artist} — {match['name']}")
                continue
            if any(row["uri"] == match["uri"] for row in resolved):
                skipped.append(f"{artist} — {title} (duplicate in requested batch)")
                continue
            resolved.append({"artist": artist, "track": match["name"], "uri": match["uri"]})
        if skipped:
            lines = [
                f'20-TRACK BATCH NOT STAGED — {p.get("name")} [{pid}]',
                f'New Spotify matches: {len(resolved)}/20; already present: {len(already_present)}; unmatched/duplicate: {len(skipped)}.',
                "No playlist changes have been made. Review the exceptions before staging.",
                "",
            ]
            lines.extend(f"FOUND: {row['artist']} — {row['track']}" for row in resolved)
            lines.extend(f"ALREADY PRESENT: {row}" for row in already_present)
            lines.extend(f"SKIPPED: {row}" for row in skipped)
            result = "\\n".join(lines)
        else:
            operations = [{"action": "add", "uris": [row["uri"] for row in resolved]}]
            confirmation = secrets.token_urlsafe(12)
            config["pending"] = {
                "playlist_id": pid, "operations": operations,
                "snapshot_id": p.get("snapshot_id"),
                "expected_uris": snapshot_uris(current),
                "confirmation": confirmation, "kind": "booze20",
            }
            manager.write(STATE, config)
            manager.audit(event="booze20_previewed", playlist_id=pid, added_count=len(resolved))
            lines = [
                f'20-TRACK BATCH PREVIEW — {p.get("name")} [{pid}]',
                f'Current items: {len(current["items"])}; additions: {len(resolved)}; already present: {len(already_present)}; after confirmation: {len(current["items"]) + len(resolved)}.',
                "No playlist changes have been made.",
                "",
            ]
            lines.extend(f'{index:02d}. {row["artist"]} — {row["track"]} [{row["uri"]}]' for index, row in enumerate(resolved, 1))
            lines.extend(f"Already present: {row}" for row in already_present)
            lines.extend(["", "To add these exact new tracks, submit confirm with this one-time code:", confirmation, "The playlist must remain unlocked and unchanged until confirmation."])
            result = "\\n".join(lines)
    elif action == "booze20_resolve_sources":
        # Read exact track URIs from known Spotify albums/playlists; no catalogue search.
        sources = command["sources"]
        if not isinstance(sources, list) or not sources or len(sources) > 20:
            fail("Rejected: sources must be a non-empty list of at most 20 records.")
        lines = ["SOURCE TRACK URI LOOKUP — read-only; no playlist changes."]
        def music_key(value):
            return "".join(ch for ch in str(value or "").casefold() if ch.isalnum())
        for source in sources:
            if not isinstance(source, dict) or set(source) != {"kind", "id", "artist", "title"}:
                fail("Rejected: each source must contain exactly kind, id, artist, and title.")
            kind, source_id, artist, title = (
                source["kind"], source["id"], source["artist"], source["title"]
            )
            if kind not in {"album", "playlist"} or not all(
                isinstance(value, str) and value.strip()
                for value in (source_id, artist, title)
            ):
                fail("Rejected: source kind, ID, artist, or title is invalid.")
            if not source_id.isalnum():
                fail("Rejected: source ID must be an alphanumeric Spotify ID.")
            if kind == "album":
                page = sp.call("GET", f"/albums/{source_id}/tracks?limit=50")
            else:
                page = sp.call(
                    "GET",
                    f"/playlists/{source_id}/items?limit=100&additional_types=track",
                )
            entries = page.get("items") or []
            matches = []
            for entry in entries:
                track = entry.get("item") or entry.get("track") or entry
                if (
                    music_key(track.get("name")) == music_key(title)
                    and any(
                        music_key(a.get("name")) == music_key(artist)
                        for a in (track.get("artists") or [])
                    )
                    and isinstance(track.get("uri"), str)
                    and track["uri"].startswith("spotify:track:")
                ):
                    matches.append(track)
            if len(matches) == 1:
                lines.append(
                    f"FOUND: {artist} — {matches[0].get('name')} [{matches[0]['uri']}]"
                )
            elif len(matches) > 1:
                lines.append(f"AMBIGUOUS: {artist} — {title} ({len(matches)} exact entries)")
            else:
                lines.append(f"NOT FOUND: {artist} — {title} in {kind} {source_id}")
        result = "\\n".join(lines)
    elif action == "booze20_uri_preview":
        # Stage a pre-resolved batch without calling the catalogue search endpoint.
        tracks = command["tracks"]
        if not isinstance(tracks, list) or not tracks or len(tracks) > 50:
            fail("Rejected: tracks must be a non-empty list of at most 50 track records.")
        pid = command["playlist_id"]
        p = owned_playlist(sp, pid, me)
        if not manager.unlocked(pid):
            fail("Blocked: playlist is LOCKED. Unlock it explicitly before previewing edits.")
        current = manager.snapshot(sp, p)
        existing = {item.get("uri") for item in current["items"] if item.get("uri")}
        def music_key(value):
            return "".join(ch for ch in str(value or "").casefold() if ch.isalnum())
        resolved, already_present, seen = [], [], set()
        for row in tracks:
            if not isinstance(row, dict) or set(row) != {"artist", "title", "uri"}:
                fail("Rejected: each track must contain exactly artist, title, and uri.")
            artist, title, uri = row["artist"], row["title"], row["uri"]
            if not all(isinstance(value, str) and value.strip() for value in (artist, title, uri)):
                fail("Rejected: track artist, title, and URI must be non-empty strings.")
            if not uri.startswith("spotify:track:"):
                fail(f"Rejected: invalid Spotify track URI for {artist} — {title}.")
            if uri in seen:
                fail(f"Rejected: duplicate URI in requested batch: {uri}")
            seen.add(uri)
            track_id = uri.rsplit(":", 1)[-1]
            metadata = sp.call("GET", f"/tracks/{urllib.parse.quote(track_id)}")
            actual_artist = any(
                music_key(a.get("name")) == music_key(artist)
                for a in (metadata.get("artists") or [])
            )
            if music_key(metadata.get("name")) != music_key(title) or not actual_artist:
                fail(
                    f"Rejected URI mismatch: requested {artist} — {title}, "
                    f"Spotify returned {', '.join(a.get('name', '') for a in metadata.get('artists', []))} "
                    f"— {metadata.get('name')}."
                )
            if uri in existing:
                already_present.append(f"{artist} — {metadata.get('name')}")
            else:
                resolved.append({"artist": artist, "track": metadata.get("name"), "uri": uri})
        if not resolved:
            result = f'URI BATCH CHECKED — {p.get("name")} [{pid}]\nAll verified tracks are already present; no changes were staged.'
        else:
            operations = [{"action": "add", "uris": [row["uri"] for row in resolved]}]
            confirmation = secrets.token_urlsafe(12)
            config["pending"] = {
                "playlist_id": pid, "operations": operations,
                "snapshot_id": p.get("snapshot_id"),
                "expected_uris": snapshot_uris(current),
                "confirmation": confirmation, "kind": "booze20",
            }
            manager.write(STATE, config)
            manager.audit(event="booze20_uri_previewed", playlist_id=pid, added_count=len(resolved))
            lines = [
                f'URI BATCH PREVIEW — {p.get("name")} [{pid}]',
                f'Current items: {len(current["items"])}; verified additions: {len(resolved)}; already present: {len(already_present)}; after confirmation: {len(current["items"]) + len(resolved)}.',
                "No playlist changes have been made.",
                "",
            ]
            lines.extend(
                f'{index:02d}. {row["artist"]} — {row["track"]} [{row["uri"]}]'
                for index, row in enumerate(resolved, 1)
            )
            lines.extend(f"Already present: {row}" for row in already_present)
            lines.extend([
                "",
                "To add these exact verified tracks, submit confirm with this one-time code:",
                confirmation,
                "The playlist must remain unlocked and unchanged until confirmation.",
            ])
            result = "\\n".join(lines)
    elif action == "horror_preview":
        # Resolve a hand-curated 46-track Halloween expansion through Spotify's
        # own catalogue, then stage it for the existing one-time confirmation flow.
        candidates = [
            ("Nekromantix", "Who Killed The Cheerleader"),
            ("Nekromantix", "Haunted Cathouse"),
            ("Nekromantix", "Trick Or Treat"),
            ("Nekromantix", "Nice Day For A Resurrection"),
            ("The Creepshow", "Zombies Ate Her Brain"),
            ("The Creepshow", "Creatures of the Night"),
            ("The Creepshow", "Grave Diggers"),
            ("The Creepshow", "The Devil's Son"),
            ("Horrorpops", "Walk Like A Zombie"),
            ("Horrorpops", "Ghouls"),
            ("Horrorpops", "Psychobitches Outta Hell"),
            ("Horrorpops", "Miss Take"),
            ("Horrorpops", "Where They Wander"),
            ("Koffin Kats", "Witch in the Woods"),
            ("Koffin Kats", "The Bottle Called"),
            ("Koffin Kats", "Graveyard Tree"),
            ("Koffin Kats", "Chainsaw Massacre"),
            ("45 Grave", "Riboflavin"),
            ("45 Grave", "Surf Bat"),
            ("45 Grave", "Evil"),
            ("45 Grave", "Partytime"),
            ("The Meteors", "Psycho for Your Love"),
            ("The Meteors", "Little Red Riding Hood"),
            ("The Meteors", "Bad Moon Rising"),
            ("The Meteors", "Wreckin' Crew"),
            ("Tiger Army", "Rose Of The Devil's Garden"),
            ("Tiger Army", "Through The Darkness"),
            ("Tiger Army", "Temptation"),
            ("The Ghastly Ones", "Haulin' Hearse"),
            ("The Ghastly Ones", "Diabolo's Theme"),
            ("The Ghastly Ones", "Ghastly Stomp"),
            ("The Ghastly Ones", "Banshee Beach"),
            ("Los Straitjackets", "Rockula"),
            ("Los Straitjackets", "The Munsters Theme"),
            ("The Fuzztones", "She's Wicked"),
            ("Bauhaus", "She's in Parties"),
            ("Bauhaus", "Dark Entries"),
            ("Roky Erickson", "Night of the Vampire"),
            ("Roky Erickson", "I Walked with a Zombie"),
            ("Deadbolt", "Psychic Voodoo Doll"),
            ("Calabrese", "Midnight Spookshow"),
            ("Zombina & The Skeletones", "Nobody Likes You (When You're Dead)"),
            ("The Cramps", "Human Fly"),
        ]
        pid = command["playlist_id"]
        p = owned_playlist(sp, pid, me)
        if not manager.unlocked(pid):
            fail("Blocked: playlist is LOCKED. Unlock it explicitly before requesting the horror expansion.")
        current = manager.snapshot(sp, p)
        existing = {item.get("uri") for item in current["items"] if item.get("uri")}
        def music_key(value):
            return "".join(ch for ch in str(value or "").casefold() if ch.isalnum())
        resolved, skipped = [], []
        for artist, title in candidates:
            query = urllib.parse.urlencode({
                "type": "track", "limit": 10,
                "q": f'artist:"{artist}" track:"{title}"',
            })
            page = sp.call("GET", "/search?" + query)
            matches = ((page or {}).get("tracks") or {}).get("items") or []
            target_artist, target_title = music_key(artist), music_key(title)
            match = next((
                track for track in matches
                if music_key(track.get("name")) == target_title
                and any(music_key(a.get("name")) == target_artist for a in (track.get("artists") or []))
                and isinstance(track.get("uri"), str)
                and track["uri"].startswith("spotify:track:")
            ), None)
            if not match:
                skipped.append(f"{artist} — {title} (no exact Spotify match)")
                continue
            if match["uri"] in existing or any(row["uri"] == match["uri"] for row in resolved):
                skipped.append(f"{artist} — {title} (already in playlist or duplicate)")
                continue
            resolved.append({"artist": artist, "track": match["name"], "uri": match["uri"]})
        if len(resolved) != len(candidates):
            lines = [
                f'HORROR EXPANSION NOT STAGED — {p.get("name")} [{pid}]',
                f'Exact Spotify matches: {len(resolved)}/{len(candidates)}; existing/duplicate/unmatched: {len(skipped)}.',
                "No playlist changes have been made. The expansion requires all requested tracks to resolve cleanly.",
                "",
            ]
            lines.extend(f"FOUND: {row['artist']} — {row['track']}" for row in resolved)
            lines.extend(f"SKIPPED: {row}" for row in skipped)
            result = "\n".join(lines)
        else:
            operations = [{"action": "add", "uris": [row["uri"] for row in resolved]}]
            confirmation = secrets.token_urlsafe(12)
            config["pending"] = {
                "playlist_id": pid, "operations": operations,
                "snapshot_id": p.get("snapshot_id"),
                "expected_uris": snapshot_uris(current),
                "confirmation": confirmation, "kind": "horror_expansion",
            }
            manager.write(STATE, config)
            manager.audit(event="horror_expansion_previewed", playlist_id=pid, added_count=len(resolved))
            lines = [
                f'HORROR EXPANSION PREVIEW — {p.get("name")} [{pid}]',
                f'Current items: {len(current["items"])}; additions: {len(resolved)}; after confirmation: {len(current["items"]) + len(resolved)}.',
                "No playlist changes have been made.",
                "",
            ]
            lines.extend(f'{index:02d}. {row["artist"]} — {row["track"]} [{row["uri"]}]' for index, row in enumerate(resolved, 1))
            lines.extend(["", "To add these exact tracks, submit confirm with this one-time code:", confirmation, "The playlist must remain unlocked and unchanged until confirmation."])
            result = "\n".join(lines)
    elif action == "daily_preview":
        import spotify_discovery as daily
        pid = command["playlist_id"]
        p = owned_playlist(sp, pid, me)
        if p.get("name", "").strip().casefold() != "tricky daily":
            fail("Blocked: daily_preview is restricted to the playlist named Tricky Daily.")
        if not manager.unlocked(pid):
            fail("Blocked: Tricky Daily is LOCKED. Unlock it explicitly before requesting a daily preview.")
        current = manager.snapshot(sp, p)
        recommendations, skipped = daily.build_discovery_recommendations(
            sp, current["items"], playlist_id=pid
        )
        feedback = daily.load_playlist_feedback(current["items"], pid)
        uris = [row["uri"] for row in recommendations]
        operations = [{"action": "replace", "uris": uris}]
        confirmation = secrets.token_urlsafe(12)
        config["pending"] = {
            "playlist_id": pid, "operations": operations,
            "snapshot_id": p.get("snapshot_id"), "expected_uris": snapshot_uris(current),
            "confirmation": confirmation, "recommendation_date": manager.stamp(), "kind": "daily",
        }
        manager.write(STATE, config)
        manager.audit(
            event="daily_recommendations_previewed",
            playlist_id=pid,
            recommendation_count=len(recommendations),
            skipped_count=len(skipped),
            scoring_version=intelligence.scoring_config()["version"],
            recommendations=[
                {
                    "uri": row["uri"], "artist": row["artist"], "track": row["track"],
                    "score": row.get("score"), "similarity": row.get("similarity"),
                    "confidence": row.get("confidence"), "why": row.get("why", []),
                }
                for row in recommendations
            ],
        )
        tier_counts = {tier: sum(1 for row in recommendations if row.get("tier") == tier) for tier in ("discovery", "rediscovery", "familiar")}
        liked_count = sum(1 for row in recommendations if row.get("liked"))
        profile = intelligence.build_playlist_profile(current["items"], feedback)
        confidence_counts = {level: sum(1 for row in recommendations if row.get("confidence") == level) for level in ("strong fit", "promising", "wildcard")}
        lines = [
            f'DAILY DISCOVERY PREVIEW — {p.get("name")} [{pid}]',
            f'Recommended tracks: {len(recommendations)}; current items: {len(current["items"])}',
            f'Mix: {tier_counts["discovery"]} unheard tracks, {tier_counts["rediscovery"]} lightly heard tracks, {tier_counts["familiar"]} familiar tracks.',
            f'{liked_count} already-Liked track(s) survived a strong ranking penalty; prior scrobbles were penalized by frequency and recency, never hard-excluded.',
            f'Confidence: {confidence_counts["strong fit"]} strong fit, {confidence_counts["promising"]} promising, {confidence_counts["wildcard"]} wildcard.',
            f'Playlist identity: {profile["artist_count"]} primary artists; metadata coverage {profile["metadata_coverage"]:.0%}; top genre signals: {", ".join(row["tag"] for row in profile["genres"][:5]) or "unavailable"}.',
            f'Playlist feedback: {feedback["removed_count"]} prior removals currently count as negative evidence; {feedback["whitelisted_count"]} re-added track(s) are whitelisted by current membership.',
            "Current playlist artists provide positive evidence; removals from this playlist only provide soft negative evidence here.",
            "Candidates come from similar artists outside the scrobble archive, resolved against Spotify; max two tracks per artist.",
            "No playlist changes have been made.",
            "",
        ]
        for index, row in enumerate(recommendations, 1):
            familiarity = "already Liked" if row.get("liked") else ("unheard" if not row.get("plays") else f'{row.get("plays")} archive plays')
            popularity = row.get("popularity")
            popularity_label = f"Spotify popularity {popularity}" if isinstance(popularity, (int, float)) else "Spotify popularity unavailable from API"
            lines.append(f'{index:02d}. {row["artist"]} — {row["track"]} [{row.get("confidence", "promising").upper()}; {row.get("tier", "discovery").upper()}; {familiarity}; similarity {row.get("similarity", 0):.2f}; {popularity_label}]')
            reasons = "; ".join(row.get("why") or [])
            if reasons:
                lines.append(f'    WHY: {reasons}')
        lines.extend(["", f'Skipped {len(skipped)} candidates already present in Tricky Daily or without a usable Spotify match.', "To replace Tricky Daily with this exact set, submit confirm with this one-time code:", confirmation, "The playlist must remain unlocked and unchanged until confirmation."])
        result = "\n".join(lines)
    elif action == "undo":
        last = config.get("last_completed") or {}
        if not last:
            fail("Nothing to undo: no completed change has a recovery snapshot.")
        pid = last.get("playlist_id")
        if not manager.unlocked(pid):
            fail("Blocked: playlist is LOCKED. Unlock it explicitly before undo.")
        p = owned_playlist(sp, pid, me)
        current_snapshot = manager.snapshot(sp, p)
        if not completed_state_matches(p, last, current_snapshot):
            fail("Undo refused: playlist contents changed after the saved operation.")
        backup_path = Path(last.get("backup", ""))
        if not backup_path.is_file():
            fail("Recovery snapshot is unavailable. Check the original workflow artifact.")
        backup_data = manager.read(backup_path, None)
        if not isinstance(backup_data, dict) or (backup_data.get("playlist") or {}).get("id") != pid:
            fail("Recovery snapshot is invalid or belongs to another playlist.")
        restore_uris = [item.get("uri") for item in backup_data.get("items", [])]
        current_snapshot = manager.snapshot(sp, p)
        if any(not isinstance(uri, str) or not uri.startswith(("spotify:track:", "spotify:episode:")) for uri in restore_uris):
            fail("Undo refused: the snapshot contains unavailable or unsupported playlist items.")
        confirmation = secrets.token_urlsafe(12)
        config["pending"] = {
            "kind": "undo", "playlist_id": pid, "snapshot_id": p.get("snapshot_id"),
            "backup": str(backup_path), "confirmation": confirmation,
            "restore_count": len(restore_uris),
            "expected_uris": snapshot_uris(current_snapshot),
        }
        manager.write(STATE, config)
        manager.audit(event="undo_previewed", playlist_id=pid, restore_count=len(restore_uris), backup=str(backup_path))
        result = (
            f'UNDO PREVIEW — {p.get("name")} [{pid}]\n'
            f'Current items: {len(current_snapshot["items"])}\n'
            f'Restore previous snapshot: {len(restore_uris)} item(s), in original order.\n'
            "No changes have been made.\n\n"
            f'To restore this snapshot, submit confirm with this one-time code: {confirmation}'
        )
    elif action == "confirm":
        pending = config.get("pending") or {};
        if not pending or not secrets.compare_digest(
            command["confirmation"], pending.get("confirmation", "")
        ):
            fail("Rejected: no matching pending preview. Run preview again.")
        pid = pending["playlist_id"]
        if not manager.unlocked(pid):
            fail("Blocked: playlist is LOCKED; preview cancelled.")
        p = owned_playlist(sp, pid, me)
        kind = pending.get("kind", "edit")
        before = manager.snapshot(sp, p)
        if not pending_state_matches(p, pending, before):
            config.pop("pending", None)
            manager.write(STATE, config)
            message = (
                "Playlist contents changed after undo preview. Run undo again to review the latest state."
                if kind == "undo"
                else "Playlist changed after preview. Preview it again before confirming."
            )
            fail(message)
        backup = manager.save_snapshot(before)
        if kind == "undo":
            manager.audit(event="undo_started", playlist_id=pid, redo_snapshot=backup, recovery_snapshot=pending["backup"])
        else:
            manager.audit(
                event="change_started", playlist_id=pid, name=p.get("name"),
                operations=pending["operations"], backup=backup, user_id=me.get("id")
            )
        # Consume the one-time confirmation before the first write.
        config.pop("pending", None)
        manager.write(STATE, config)
        manager.audit(event="confirmation_consumed", playlist_id=pid, backup=backup, kind=kind)
        try:
            if kind == "undo":
                restore_data = manager.read(Path(pending["backup"]), None)
                if (
                    not isinstance(restore_data, dict)
                    or not isinstance(restore_data.get("items"), list)
                ):
                    raise manager.ManagerError(
                        "Recovery snapshot is unavailable in this workflow run; undo was stopped before restoration."
                    )
                replace_playlist(sp, pid, [item["uri"] for item in restore_data["items"]])
            else:
                execute(sp, pid, pending["operations"])
                cleanup_count = 0
                if config.get("playlists", {}).get(pid, {}).get("cleanup") is True:
                    cleanup_count = cleanup_duplicates(sp, pid)
                if kind == "daily":
                    current_description = p.get("description") or ""
                    choices = [line for line in DAILY_DESCRIPTIONS if line != current_description]
                    if not choices:
                        raise manager.ManagerError("No alternate Tricky Daily description is available.")
                    new_description = secrets.choice(choices)
                    sp.call("PUT", f"/playlists/{pid}", {"description": new_description})
                    manager.audit(
                        event="daily_description_updated",
                        playlist_id=pid,
                        description=new_description,
                    )
            updated = owned_playlist(sp, pid, me)
        except Exception as operation_error:
            # A multi-request edit can fail after Spotify has accepted some writes.
            # Preserve an undo pointer to the pre-change snapshot even on partial failure.
            try:
                interrupted = owned_playlist(sp, pid, me)
                interrupted_snapshot = manager.snapshot(sp, interrupted)
                config["last_completed"] = {
                    "playlist_id": pid,
                    "backup": backup,
                    "backup_run_id": os.environ.get("GITHUB_RUN_ID", ""),
                    "after_snapshot_id": interrupted.get("snapshot_id"),
                    "after_uris": snapshot_uris(interrupted_snapshot),
                    "kind": "partial",
                }
                manager.write(STATE, config)
                manager.audit(
                    event="change_interrupted",
                    playlist_id=pid,
                    backup=backup,
                    kind=kind,
                    error_type=type(operation_error).__name__,
                )
            except Exception as recovery_error:
                manager.audit(
                    event="recovery_state_capture_failed",
                    playlist_id=pid,
                    backup=backup,
                    error_type=type(recovery_error).__name__,
                )
            raise
        updated_snapshot = manager.snapshot(sp, updated)
        config["last_completed"] = {
            "playlist_id": pid, "backup": backup,
            "backup_run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "after_snapshot_id": updated.get("snapshot_id"),
            "after_uris": snapshot_uris(updated_snapshot),
            "kind": kind,
        }
        manager.write(STATE, config)
        manager.audit(event="change_completed", playlist_id=pid, backup=backup, kind=kind)
        count = (updated.get("items") or updated.get("tracks") or {}).get("total", "?")
        verb = "Restored the previous snapshot of" if kind == "undo" else "Completed the confirmed changes to"
        cleanup_note = (
            f" Automatic duplicate cleanup removed {cleanup_count} surplus copy/copies."
            if kind != "undo" and "cleanup_count" in locals() and cleanup_count
            else (
                " Automatic duplicate cleanup found nothing to remove."
                if kind != "undo" and config.get("playlists", {}).get(pid, {}).get("cleanup") is True
                else ""
            )
        )
        result = (
            f'{verb} "{updated.get("name")}". '
            f"Current status: {count} items; UNLOCKED.{cleanup_note} "
            "A pre-change recovery snapshot was saved as a workflow artifact."
        )
    else:
        manager.audit(event="status_requested")
        result = "Playlist status:"

    if action in {"status", "lock_all", "lock", "unlock"}:
        lines = [result, "", "| Playlist | Items | Lock | Auto-cleanup | ID |", "|---|---:|---|---|---|"]
        for p in playlists:
            pid = p["id"]
            is_owned = (p.get("owner") or {}).get("id") == me.get("id")
            state = config["playlists"].get(pid, {}).get("state", "locked") if is_owned else "locked (not owned)"
            count = (p.get("items") or p.get("tracks") or {}).get("total", "?")
            safe_name = str(p.get("name", "")).replace("|", "\\|").replace("\n", " ")
            cleanup_state = "ON" if config["playlists"].get(pid, {}).get("cleanup") is True else "OFF"
            lines.append("| " + safe_name + " | " + str(count) + " | " + state.upper() + " | " + cleanup_state + " | `" + pid + "` |")
        result = "\n".join(lines)

    if getattr(sp, "refresh_token_rotated", False):
        result += (
            "\\n\\nWARNING: Spotify issued a replacement refresh token during this run. "
            "The temporary runner cannot update the repository secret. Before the next command, "
            "reauthorize the playlist manager locally and replace SPOTIFY_REFRESH_TOKEN in "
            "GitHub Actions Secrets."
        )

    print(result)
    import uuid
    delimiter = "RESULT_" + uuid.uuid4().hex
    Path(os.environ["GITHUB_OUTPUT"]).write_text(
        f"result<<{delimiter}\n{result}\n{delimiter}\n", encoding="utf-8"
    )


if __name__ == "__main__":
    try:
        main()
    except (manager.ManagerError, OSError, KeyError, ValueError, urllib.error.URLError) as error:
        print("ERROR:", error, file=sys.stderr)
        raise SystemExit(1)
