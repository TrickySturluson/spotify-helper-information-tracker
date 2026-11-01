import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"/"spotify"))
import spotify_listening_trends as trends

class ListeningTrendTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,1,tzinfo=timezone.utc)
    def event(self,artist,days):
        return {"artist":artist,"timestamp":int((self.now-timedelta(days=days)).timestamp())}
    def test_recent_artist_activity_compares_to_previous_60_days(self):
        rows=[self.event("Artist A",3) for _ in range(12)]
        rows += [self.event("Artist A",45) for _ in range(12)]
        result=trends.build_trends(rows,{"a":{"artist":"Artist A","tags":["shoegaze"]}},self.now)
        row=result["artists"]["artist a"]
        self.assertEqual(row["plays_30d"],12)
        self.assertEqual(row["plays_previous_60d"],12)
        self.assertEqual(row["trend_confidence"],"high")
        self.assertEqual(row["tags"],["shoegaze"])
        self.assertEqual(result["coverage"]["status"],"available")
    def test_short_term_spike_compares_to_previous_week(self):
        rows=[self.event("Artist",2) for _ in range(10)]
        rows += [self.event("Artist",10) for _ in range(2)]
        result=trends.build_trends(rows,{},self.now)
        self.assertGreater(result["artists"]["artist"]["momentum_7d"],0.5)
        self.assertEqual(result["artists"]["artist"]["plays_previous_7d"],2)
    def test_genre_trends_are_aggregated_from_artist_metadata(self):
        rows=[self.event("Dream Artist",3) for _ in range(10)]
        rows += [self.event("Dream Artist",45) for _ in range(5)]
        result=trends.build_trends(rows,{"a":{"artist":"Dream Artist","genres":["dream pop"]}},self.now)
        genre=result["genres"][0]
        self.assertEqual(genre["tag"],"dream pop")
        self.assertEqual(genre["plays_30d"],10)
        self.assertEqual(genre["plays_previous_60d"],5)
    def test_sparse_history_is_unknown_not_a_false_spike(self):
        result=trends.build_trends([self.event("New Artist",1)],{},self.now)
        affinity,confidence,reasons=trends.candidate_affinity("New Artist",result)
        self.assertEqual((affinity,confidence,reasons),(0.0,"low",[]))
    def test_old_favorite_remains_in_all_time_baseline(self):
        result=trends.build_trends([self.event("Old Favorite",180) for _ in range(50)],{},self.now)
        row=result["artists"]["old favorite"]
        self.assertEqual(row["plays_all_time"],50)
        self.assertIsNone(row["momentum_30d"])
    def test_candidate_affinity_is_confidence_gated(self):
        rows=[self.event("Rising",2) for _ in range(12)]+[self.event("Rising",50) for _ in range(12)]
        result=trends.build_trends(rows,{},self.now)
        affinity,confidence,reasons=trends.candidate_affinity("Rising",result)
        self.assertGreater(affinity,0.5)
        self.assertEqual(confidence,"high")
        self.assertTrue(reasons)
    def test_generate_writes_report_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); src=root/"scrobbles.json"; prof=root/"profiles.json"; out=root/"nested"/"trends.json"
            src.write_text(json.dumps([self.event("Artist",1) for _ in range(12)]),encoding="utf-8")
            prof.write_text(json.dumps({"a":{"artist":"Artist","tags":["dream pop"]}}),encoding="utf-8")
            report=trends.generate(src,prof,out,self.now)
            self.assertTrue(out.is_file())
            self.assertEqual(report["artists"]["artist"]["tags"],["dream pop"])

if __name__=="__main__": unittest.main()

# FILE OVERVIEW
# Purpose: Regression tests for 7/30/90-day trend windows, baselines, genre
# momentum, confidence gating, sparse-history handling and report generation.
