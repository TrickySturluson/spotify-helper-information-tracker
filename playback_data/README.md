# Measured Spotify playback — file overview

This directory is reserved for raw or canonical measured Spotify playback records collected by the playback tracker. It is intentionally separate from `data/scrobbles.json`, which is Last.fm listening history, and from `assistant_data/playback/`, which contains derived playback summaries.

The directory may contain only `.gitkeep` until playback records are collected. Do not treat an empty directory as evidence of no listening; it means this source has not populated the archive. The collector is maintained in `scripts/spotify/spotify_playback_tracker.py`; see its file overview and related workflow for operation and data format.
