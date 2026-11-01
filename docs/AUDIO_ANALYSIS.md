# SHIT Audio Analysis

SHIT now has an optional local-file audio analysis layer built around Essentia.
It measures music from audio files the user already has legitimate access to;
it does **not** download, rip, or extract Spotify streams.

## Measurements

- Tempo estimate (BPM), beat positions, alternate BPM estimates, and beat-tracker confidence.
- EBU R128 integrated loudness (LUFS) and loudness range (LU).
- Momentary and short-term loudness series where supplied by the installed Essentia build.
- A configurable RMS/peak envelope in fixed time windows (default 10 seconds).
- Segment RMS spread and a basic dynamic-complexity descriptor.

LUFS describes the loudness of the audio program, not the volume knob or playback gain.
Segment RMS/peak values describe relative changes within a recording; they are not calibrated SPL.
BPM can be half/double-time ambiguous and confidence must be retained.

## Install and run locally

Install the optional dependencies:

```bash
python -m pip install -r requirements-audio-analysis.txt
```

Name files `Artist - Track.ext`, then run:

```bash
python audio_analysis.py ./audio_inbox
```

Or analyze one file:

```bash
python audio_analysis.py "./audio_inbox/Messer Chups - Zombie Twist.flac"
```

Output defaults to `assistant_data/music/audio_profiles.json`. Existing profiles are
merged by normalized artist/title key, so rerunning with a new batch does not discard
previously analyzed tracks. Use `--segment-seconds 5` for a more detailed envelope
or `--output path/to/file.json` to select another destination.

## Playlist sorter integration

`spotify_playlist_sequencer.py` loads this profile file automatically. Measured BPM
and integrated LUFS can contribute to the energy estimate; loudness range and
dynamic complexity are reported as additional evidence. Spotify-provided features,
when present in an item export, take precedence over locally measured values.

The current sorter does not yet perform true DJ beatmatching or automatic gain
normalization. Segment envelopes are preserved for future transition planning;
the next iteration can compare outro-to-intro levels and identify quiet-to-loud
builds/drops rather than treating a whole track as one static value.

## Data and licensing

Audio files remain wherever the user stores them and are not copied into the
profile output. Only measurements, source filename, and timestamps are saved.
Essentia is AGPL-3.0-only (with separate commercial licensing available from its
maintainers); review the license before redistributing or embedding it in a
closed-source product.
