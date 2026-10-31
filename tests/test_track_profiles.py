import unittest
from unittest.mock import patch

import build_track_profiles as profiles


class TrackProfileTests(unittest.TestCase):
    def test_track_identity_matches_metadata_builder_fallback(self):
        row = {"artist": "Example Artist", "track": "Example Song"}
        aid = profiles.artist_id(row)
        self.assertEqual(aid, "name:" + __import__("hashlib").sha1(b"example artist").hexdigest()[:16])
        self.assertEqual(
            profiles.track_id(row, aid),
            "track:" + __import__("hashlib").sha1((aid + "\0example song").encode()).hexdigest()[:16],
        )

    def test_lastfm_tags_preserve_counts_and_source(self):
        payload = {"toptags": {"@attr": {"artist": "Example Artist", "track": "Example Song"},
                               "tag": [{"name": "dreamy", "count": "42"}, {"name": "shoegaze", "count": "7"}]}}
        with patch.object(profiles, "request_json", return_value=payload):
            tags, status = profiles.lastfm_tags({"artist": "Example Artist", "track": "Example Song"})
        self.assertEqual(status, "matched")
        self.assertEqual(tags[0], {"tag": "dreamy", "count": 42, "source": "Last.fm track.getTopTags"})

    def test_lastfm_identity_mismatch_is_not_accepted(self):
        payload = {"toptags": {"@attr": {"artist": "Different Artist", "track": "Example Song"},
                               "tag": [{"name": "pop", "count": "99"}]}}
        with patch.object(profiles, "request_json", return_value=payload):
            tags, status = profiles.lastfm_tags({"artist": "Example Artist", "track": "Example Song"})
        self.assertEqual(tags, [])
        self.assertEqual(status, "identity_mismatch")


    def test_mbid_http_400_falls_back_to_exact_artist_and_track(self):
        from urllib.error import HTTPError
        from io import BytesIO

        mbid = "12345678-1234-1234-1234-123456789abc"
        item = {"artist": "Example Artist", "track": "Example Song", "track_mbid": mbid}
        payload = {"toptags": {"@attr": {"artist": "Example Artist", "track": "Example Song"},
                               "tag": [{"name": "dream pop", "count": "12"}]}}
        error = HTTPError("https://ws.audioscrobbler.com/2.0/", 400, "Bad Request", {}, BytesIO(b"{}"))
        with patch.object(profiles, "request_json", side_effect=[error, payload]) as request:
            tags, status = profiles.lastfm_tags(item)
        self.assertEqual(status, "matched")
        self.assertEqual(tags[0]["tag"], "dream pop")
        first_params = request.call_args_list[0].args[1]
        second_params = request.call_args_list[1].args[1]
        self.assertEqual(first_params["mbid"], mbid)
        self.assertNotIn("mbid", second_params)
        self.assertEqual((second_params["artist"], second_params["track"]), ("Example Artist", "Example Song"))

    def test_mbid_http_404_falls_back_but_still_checks_identity(self):
        from urllib.error import HTTPError
        from io import BytesIO

        item = {"artist": "Example Artist", "track": "Example Song",
                "track_mbid": "12345678-1234-1234-1234-123456789abc"}
        wrong_identity = {"toptags": {"@attr": {"artist": "Other Artist", "track": "Example Song"},
                                      "tag": [{"name": "pop", "count": "99"}]}}
        error = HTTPError("https://ws.audioscrobbler.com/2.0/", 404, "Not Found", {}, BytesIO(b"{}"))
        with patch.object(profiles, "request_json", side_effect=[error, wrong_identity]):
            tags, status = profiles.lastfm_tags(item)
        self.assertEqual(tags, [])
        self.assertEqual(status, "identity_mismatch")

    def test_http_errors_respect_retry_cooldown(self):
        now = 1_800_000_000
        self.assertFalse(profiles.should_retry_lastfm({"lastfm_status": "http_400",
                                                       "retry_after": now + 30 * 86400}, now))
        self.assertFalse(profiles.should_retry_lastfm({"lastfm_status": "http_404",
                                                       "retry_after": now + 30 * 86400}, now))
        self.assertTrue(profiles.should_retry_lastfm({"lastfm_status": "http_400",
                                                      "retry_after": now - 1}, now))
        self.assertFalse(profiles.should_retry_lastfm({"lastfm_status": "matched",
                                                       "retry_after": 0}, now))
        self.assertFalse(profiles.should_retry_lastfm({"lastfm_status": "http_500",
                                                       "retry_after": now + 3600}, now))

    def test_musicbrainz_requires_existing_exact_recording_mbid(self):
        with patch.object(profiles, "request_json") as request:
            tags, genres, status = profiles.musicbrainz_tags({"track": "Song"})
        self.assertEqual((tags, genres, status), ([], [], "no_recording_mbid"))
        request.assert_not_called()

    def test_musicbrainz_source_provenance_is_preserved(self):
        mbid = "12345678-1234-1234-1234-123456789abc"
        payload = {"id": mbid, "tags": [{"name": "haunting", "count": 4}],
                   "genres": [{"name": "alternative", "count": 2}]}
        with patch.object(profiles, "request_json", return_value=payload):
            tags, genres, status = profiles.musicbrainz_tags({"track_mbid": mbid})
        self.assertEqual(status, "matched")
        self.assertEqual(tags[0]["source"], "MusicBrainz recording tag")
        self.assertEqual(genres[0]["source"], "MusicBrainz recording genre")


if __name__ == "__main__":
    unittest.main()
