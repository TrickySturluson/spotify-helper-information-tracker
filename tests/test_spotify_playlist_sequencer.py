import unittest

import spotify_playlist_sequencer as sequencer


class PlaylistSequencerTests(unittest.TestCase):
    def test_audio_energy_dominates_order(self):
        rows = [
            {"uri": "spotify:track:high", "name": "Loud", "artists": ["Artist"],
             "audio_features": {"energy": 0.95, "tempo": 170, "loudness": -4}},
            {"uri": "spotify:track:low", "name": "Quiet", "artists": ["Artist"],
             "audio_features": {"energy": 0.08, "tempo": 65, "loudness": -29}},
        ]
        result = sequencer.sequence_tracks(rows)
        self.assertEqual([r["item"]["name"] for r in result], ["Quiet", "Loud"])
        self.assertGreater(result[1]["score"], result[0]["score"])
        self.assertEqual(result[0]["confidence"], "high")

    def test_track_tags_are_preferred_to_artist_mood(self):
        item = {"uri": "spotify:track:1", "name": "Track", "artists": ["Artist"]}
        artists = {"artist": {"tags": [{"tag": "calm"}]}}
        tracks = {("artist", "track"): {"lastfm_tags": [{"tag": "aggressive"}]}}
        result = sequencer.score_track(item, artists, tracks)
        self.assertIn("aggressive", " ".join(result["evidence"]))
        self.assertNotIn("artist-level mood fallback", " ".join(result["evidence"]))

    def test_missing_metadata_is_explicitly_unknown(self):
        result = sequencer.score_track({"uri": "spotify:track:1", "name": "Unknown", "artists": ["No Profile"]})
        self.assertEqual(result["confidence"], "unknown")
        self.assertEqual(result["score"], 50.0)


    def test_theme_grouping_is_available_without_replacing_energy_scores(self):
        rows = [
            {"uri": "spotify:track:b", "name": "B", "artists": ["Artist B"],
             "audio_features": {"energy": 0.51}},
            {"uri": "spotify:track:a", "name": "A", "artists": ["Artist A"],
             "audio_features": {"energy": 0.52}},
        ]
        artists = {
            "artist a": {"themes": ["dreamlike"]},
            "artist b": {"themes": ["nocturnal"]},
        }
        result = sequencer.sequence_tracks(rows, artist_profiles=artists, group_by="theme")
        self.assertEqual({row["sequence_group"] for row in result}, {"dreamlike", "nocturnal"})
        self.assertLessEqual(abs(result[1]["score"] - result[0]["score"]), 10)

    def test_confidence_summary_counts_unknown_metadata(self):
        rows = [
            {"confidence": "high"},
            {"confidence": "low"},
            {"confidence": "unknown"},
            {"confidence": "unknown"},
        ]
        self.assertEqual(
            sequencer.confidence_summary(rows),
            {"high": 1, "medium": 0, "low": 1, "unknown": 2},
        )

    def test_sort_modes_include_atmosphere_style_narrative_and_discovery(self):
        rows = [
            {"uri": "spotify:track:1", "name": "Soft", "artists": ["Rare"]},
            {"uri": "spotify:track:2", "name": "Loud", "artists": ["Popular"]},
            {"uri": "spotify:track:3", "name": "Dark", "artists": ["Dark Artist"]},
        ]
        artists = {
            "rare": {"play_count": 12, "lastfm_tags": [{"tag": "dreamy"}], "genres": ["dream pop"], "themes": ["dreamlike"]},
            "popular": {"play_count": 900, "lastfm_tags": [{"tag": "energetic"}], "genres": ["punk"], "themes": ["rebellious"]},
            "dark artist": {"play_count": 80, "lastfm_tags": [{"tag": "dark"}], "genres": ["darkwave"], "themes": ["nocturnal"]},
        }
        atmosphere = sequencer.sequence_tracks(rows, artists, mode="atmosphere")
        self.assertEqual(atmosphere[0]["sequence_group"], "dreamy")
        style = sequencer.sequence_tracks(rows, artists, mode="style")
        self.assertEqual({row["sequence_group"] for row in style}, {"dream pop", "punk", "darkwave"})
        narrative = sequencer.sequence_tracks(rows, artists, mode="narrative")
        self.assertEqual(narrative[0]["sequence_group"], "act-1")
        discovery = sequencer.sequence_tracks(rows, artists, mode="discovery")
        self.assertEqual(discovery[0]["artist"], "Rare")

    def test_hybrid_keeps_broad_energy_bands_in_order(self):
        rows = [
            {"uri": "spotify:track:high", "name": "High", "artists": ["A"],
             "audio_features": {"energy": 0.91}},
            {"uri": "spotify:track:low", "name": "Low", "artists": ["B"],
             "audio_features": {"energy": 0.12}},
        ]
        result = sequencer.sequence_tracks(rows, mode="hybrid")
        self.assertEqual([row["item"]["name"] for row in result], ["Low", "High"])

    def test_reorder_plan_preserves_duplicates_and_transforms_order(self):
        current = ["a", "b", "a", "c"]
        desired = ["a", "a", "c", "b"]
        operations = sequencer.build_reorder_operations(current, desired)
        working = list(current)
        for op in operations:
            moved = working.pop(op["range_start"])
            working.insert(op["insert_before"], moved)
        self.assertEqual(working, desired)

    def test_reorder_rejects_changed_playlist_membership(self):
        with self.assertRaises(ValueError):
            sequencer.build_reorder_operations(["a", "b"], ["a", "c"])


    def test_smooth_is_default_and_hybrid_is_compatibility_alias(self):
        rows = [
            {"uri": "a", "name": "A", "artists": ["A"], "audio_features": {"energy": .1}},
            {"uri": "b", "name": "B", "artists": ["B"], "audio_features": {"energy": .5}},
            {"uri": "c", "name": "C", "artists": ["C"], "audio_features": {"energy": .2}},
            {"uri": "d", "name": "D", "artists": ["D"], "audio_features": {"energy": .9}},
        ]
        self.assertEqual(sequencer.sequence_tracks(rows), sequencer.sequence_tracks(rows, mode="hybrid"))
        self.assertEqual({r["item"]["uri"] for r in sequencer.sequence_tracks(rows)}, set("abcd"))

    def test_peak_position_and_shape(self):
        curve = [sequencer.target_energy(i, 100, peak_position=85) for i in range(100)]
        self.assertAlmostEqual(curve[85], curve[98])
        self.assertNotEqual(
            sequencer.target_energy(70, 100, peak_shape="sharp"),
            sequencer.target_energy(70, 100, peak_shape="gradual"),
        )
        self.assertNotEqual(
            sequencer.target_energy(70, 100, peak_shape="sustained"),
            sequencer.target_energy(70, 100, peak_shape="gradual"),
        )

    def test_journey_shapes(self):
        self.assertGreater(sequencer.target_energy(0, 20, "falling"), sequencer.target_energy(19, 20, "falling"))
        self.assertLess(sequencer.target_energy(0, 20, "rising"), sequencer.target_energy(19, 20, "rising"))
        self.assertAlmostEqual(sequencer.target_energy(0, 20, "steady"), sequencer.target_energy(19, 20, "steady"))
        self.assertLess(sequencer.target_energy(0, 100, "wave"), sequencer.target_energy(50, 100, "wave"))

    def test_opener_closer_and_pinned_track(self):
        rows = [
            {"uri": x, "name": x, "artists": [x], "audio_features": {"energy": energy}}
            for x, energy in [("a", .1), ("b", .9), ("c", .3), ("d", .8), ("e", .2)]
        ]
        result = sequencer.sequence_tracks(rows, opener_uri="b", closer_uri="a", pinned_uris={"c"})
        uris = [r["item"]["uri"] for r in result]
        self.assertEqual(uris[0], "b")
        self.assertEqual(uris[-1], "a")
        self.assertEqual(uris[2], "c")

    def test_sections_keep_all_tracks_and_add_soft_affinity(self):
        rows = [{"uri": x, "name": x, "artists": [x]} for x in "abcd"]
        result = sequencer.sequence_tracks(rows, sections={"Opening": ["a", "b"], "Finish": ["c", "d"]})
        self.assertEqual({r["item"]["uri"] for r in result}, set("abcd"))
        self.assertTrue(all("section_groups" in row for row in result))

    def test_transition_report_explains_handoff_and_uncertainty(self):
        a = {"score": 40, "confidence": "medium", "artist": "A", "vibe_groups": ["dreamy"], "genre_groups": ["dream pop"], "theme_groups": ["dreamlike"]}
        b = {"score": 45, "confidence": "medium", "artist": "B", "vibe_groups": ["dreamy"], "genre_groups": ["dream pop"], "theme_groups": ["dreamlike"]}
        report = sequencer.transition_report(a, b)
        self.assertEqual(report["label"], "gentle")
        self.assertIn("dreamy", report["shared_moods"])
        self.assertEqual(sequencer.transition_report(dict(a, confidence="unknown"), b)["confidence"], "limited")

    def test_transition_summary_flags_potential_jump(self):
        rows = [
            {"score": 5, "confidence": "low", "artist": "a", "vibe_groups": [], "genre_groups": [], "theme_groups": []},
            {"score": 98, "confidence": "unknown", "artist": "b", "vibe_groups": [], "genre_groups": [], "theme_groups": []},
        ]
        self.assertEqual(sequencer.transition_summary(rows)["potential_jumps"], 1)


    def test_ordered_sections_are_softly_preferred(self):
        first = {"score": 50, "confidence": "medium", "artist": "A", "vibe_groups": [],
                 "genre_groups": [], "theme_groups": [], "section_groups": ["section:0"], "section_index": 0}
        second = {"score": 50, "confidence": "medium", "artist": "B", "vibe_groups": [],
                  "genre_groups": [], "theme_groups": [], "section_groups": ["section:1"], "section_index": 1}
        forward = sequencer._sequence_objective([first, second], "steady", 85, "gradual", 0, 0)
        backward = sequencer._sequence_objective([second, first], "steady", 85, "gradual", 0, 0)
        self.assertLess(forward, backward)

    def test_all_tracks_can_be_fixed_by_opening_and_closing_anchors(self):
        rows = [
            {"uri": "start", "name": "Start", "artists": ["A"]},
            {"uri": "end", "name": "End", "artists": ["B"]},
        ]
        result = sequencer.sequence_tracks(rows, opener_uri="start", closer_uri="end")
        self.assertEqual([row["item"]["uri"] for row in result], ["start", "end"])


    def test_unknown_anchor_uri_is_rejected(self):
        rows = [{"uri": "present", "name": "Present", "artists": ["A"]}]
        with self.assertRaisesRegex(ValueError, "not in this playlist"):
            sequencer.sequence_tracks(rows, opener_uri="missing")

    def test_exported_lyric_themes_feed_transition_theme_groups(self):
        profiles = {}
        exported = [{
            "artist": "Night Club",
            "track": "Vampires",
            "themes": {"vampire": {"count": 3}, "nightlife_clubbing": {"count": 2}},
            "source_count": 2,
        }]
        sequencer.merge_lyric_features(profiles, exported)
        item = {"uri": "spotify:track:1", "name": "Vampires", "artists": ["Night Club"]}
        scored = sequencer.score_track(item, track_profiles=profiles)
        self.assertIn("vampire", scored["theme_groups"])
        self.assertIn("nightlife_clubbing", scored["theme_groups"])
        self.assertTrue(any("lyric-theme evidence" in row for row in scored["evidence"]))

    def test_lyric_themes_are_preserved_even_when_energy_is_unknown(self):
        profiles = {("night club", "vampires"): {
            "lyric_analysis": {"themes": {"vampire": {"count": 3}}}
        }}
        scored = sequencer.score_track(
            {"uri": "spotify:track:1", "name": "Vampires", "artists": ["Night Club"]},
            track_profiles=profiles,
        )
        self.assertEqual(scored["confidence"], "unknown")
        self.assertIn("vampire", scored["theme_groups"])

    def test_lastfm_artist_tags_are_used_as_low_confidence_mood_fallback(self):
        item = {"uri": "spotify:track:1", "name": "Track", "artists": ["Artist"]}
        artists = {"artist": {"tags": [{"tag": "energetic"}, {"tag": "punk"}], "genres": ["punk"]}}
        result = sequencer.score_track(item, artist_profiles=artists)
        self.assertIn("artist-level mood fallback", " ".join(result["evidence"]))
        self.assertIn("energetic", result["vibe_groups"])
        self.assertEqual(result["confidence"], "medium")

    def test_rising_journey_reaches_and_holds_a_sustained_finale(self):
        curve = [sequencer.target_energy(i, 100, "rising", peak_position=85, peak_shape="gradual")
                 for i in range(100)]
        self.assertTrue(all(left <= right for left, right in zip(curve, curve[1:])))
        self.assertAlmostEqual(curve[-1], 0.96)
        self.assertEqual(curve[85], curve[-1])

    def test_genre_family_estimates_support_surf_club_and_heavy_sections(self):
        def score(artist, genre):
            return sequencer.score_track(
                {"uri": "spotify:track:1", "name": "Track", "artists": [artist]},
                artist_profiles={artist.casefold(): {"genres": [genre]}},
            )["score"]
        self.assertEqual(score("Surf Artist", "surf rock"), 62.0)
        self.assertEqual(score("Club Artist", "synthwave"), 72.0)
        self.assertEqual(score("Heavy Artist", "industrial metal"), 78.0)

    def test_same_artist_transition_has_a_diversity_penalty(self):
        base = {"score": 60, "vibe_groups": ["energetic"], "genre_groups": ["punk"],
                "theme_groups": ["horror"], "artist": "A"}
        same = dict(base, artist="A")
        different = dict(base, artist="B")
        self.assertGreater(
            sequencer._transition_cost(base, same),
            sequencer._transition_cost(base, different),
        )

    def test_smooth_sort_respects_the_three_act_section_order(self):
        rows = []
        for uri, section in [("c", 2), ("b", 1), ("a", 0)]:
            rows.append({
                "item": {"uri": uri}, "score": 60, "original_index": len(rows),
                "vibe_groups": [], "genre_groups": [], "theme_groups": [],
                "section_index": section, "section_name": str(section),
            })
        ordered = sequencer._smooth_order(rows, journey="rising")
        self.assertEqual([row["item"]["uri"] for row in ordered], ["a", "b", "c"])

    def test_smooth_order_interleaves_same_artist_tracks_when_possible(self):
        rows = []
        for uri, artist in [("a1", "Messer Chups"), ("a2", "Messer Chups"), ("b", "The Ghastly Ones")]:
            rows.append({
                "item": {"uri": uri}, "artist": artist, "score": 60,
                "original_index": len(rows), "vibe_groups": [],
                "genre_groups": [], "theme_groups": [], "section_index": 0,
            })
        ordered = sequencer._smooth_order(rows, journey="steady")
        artists = [row["artist"] for row in ordered]
        self.assertNotEqual(artists[0], artists[1])
        self.assertNotEqual(artists[1], artists[2])

    def test_explicit_sections_remain_contiguous_and_in_declared_order(self):
        items = [
            {"uri": uri, "name": uri, "artists": [artist]}
            for uri, artist in [
                ("f2", "Final Artist"), ("c2", "Club Artist"),
                ("f1", "Final Artist"), ("o2", "Opening Artist"),
                ("c1", "Club Artist"), ("o1", "Opening Artist"),
            ]
        ]
        sections = {
            "Opening": ["o1", "o2"],
            "Club": ["c1", "c2"],
            "Finale": ["f1", "f2"],
        }
        result = sequencer.sequence_tracks(items, sections=sections)
        ranks = {"o1": 0, "o2": 0, "c1": 1, "c2": 1, "f1": 2, "f2": 2}
        actual = [ranks[row["item"]["uri"]] for row in result]
        self.assertEqual(actual, sorted(actual))

    def test_section_sorting_uses_the_global_rising_energy_curve(self):
        high = {"score": 95, "artist": "High", "vibe_groups": [],
                "genre_groups": [], "theme_groups": [], "section_index": 2}
        low = {"score": 50, "artist": "Low", "vibe_groups": [],
               "genre_groups": [], "theme_groups": [], "section_index": 2}
        high_first = sequencer._sequence_objective(
            [high, low], "rising", 85, "gradual", 0, 0, position_offset=80, total_count=100
        )
        low_first = sequencer._sequence_objective(
            [low, high], "rising", 85, "gradual", 0, 0, position_offset=80, total_count=100
        )
        self.assertLess(high_first, low_first)


if __name__ == "__main__":
    unittest.main()
