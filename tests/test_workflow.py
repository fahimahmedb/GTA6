import csv
import io
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import buffer_draft
import metrics
import pipeline
import verified_sources as sources

NOW = datetime(2026, 11, 18, 17, tzinfo=timezone.utc)
FACT = {"status": "confirmed", "valid_until": (NOW + timedelta(hours=2)).isoformat()}


class WorkflowTests(unittest.TestCase):
    def test_http_200_without_evidence_blocks(self):
        results = sources.verify({"duo": {"claim": "x", "sources": [sources.GAME]}},
                                 {sources.GAME: {"http_status": 200, "text": "Welcome!"}})
        self.assertEqual(results["duo"]["status"], "unverified")

    def test_disagreeing_release_dates_block(self):
        pages = {
            sources.SUPPORT: {
                "http_status": 200, "collected_at_utc": NOW.isoformat(),
                "text": "Will release midnight local time on November 19, 2026, on PlayStation 5 and Xbox Series X|S.",
            },
            sources.GAME: {
                "http_status": 200, "collected_at_utc": NOW.isoformat(),
                "text": "Coming November 20, 2026",
            },
        }
        result = sources.verify({"release-fr": {"claim": "x", "sources": list(pages)}}, pages)
        self.assertEqual(result["release-fr"]["status"], "conflict")

    def test_script_text_cannot_be_evidence(self):
        document = sources.Document()
        document.feed("<script>coming November 19, 2026</script><p>No announcement</p>")
        self.assertEqual(document.words, ["No announcement"])

    def test_news_discovery_deduplicates_id_and_rejects_nonofficial(self):
        page = {"http_status": 200, "url": sources.GAME, "links": [
            ("/newswire/article/a23x?utm_medium=ref", "A"),
            ("/newswire/article/a23x/slug#here", "Same article"),
            ("https://example.org/newswire/article/pretend", "False source"),
        ]}
        result = sources.discover({sources.GAME: page})
        self.assertEqual(result, [{"url": "https://www.rockstargames.com/newswire/article/a23x",
                                   "title": "A", "state": "discovered"}])

    def test_expired_announcement_and_stale_evidence_stay_out(self):
        post = {"fact_ids": ["launch"], "valid_until": "2026-11-19T00:00:00+01:00"}
        self.assertEqual(pipeline.eligibility(post, {"launch": FACT}, NOW)[0], "READY_LOCAL")
        self.assertEqual(pipeline.eligibility(post, {"launch": FACT}, NOW + timedelta(hours=2))[0], "BLOCK")
        self.assertEqual(pipeline.eligibility(post, {"launch": FACT}, NOW + timedelta(hours=6))[0], "EXPIRED")

    def test_cadence_is_paris_and_bounded(self):
        slots = pipeline.proposed_slots(NOW, list(range(10)))
        self.assertEqual(len(slots), 7)
        self.assertEqual(slots[0][1].isoformat(), "2026-11-18T19:00:00+01:00")
        self.assertEqual(slots[-1][1].day, 24)

    def test_upsert_keeps_one_queue_line_per_destination(self):
        with sqlite3.connect(":memory:") as db, tempfile.TemporaryDirectory() as root:
            db.executescript(pipeline.SCHEMA)
            post = {"id": "replay", "cover": "replay", "fact_ids": ["only"]}
            fake = {"revision": "version", "sha256": "digest"}
            with patch.object(pipeline, "prepare_pack", return_value=fake):
                first = pipeline.plan({}, [post], {"facts": {"only": FACT}}, db, Path(root), NOW)
                second = pipeline.plan({}, [post], {"facts": {"only": FACT}}, db, Path(root), NOW)
            self.assertEqual(first["queue"], second["queue"])
            self.assertEqual(db.execute("SELECT COUNT(*) FROM local_queue").fetchone()[0], 3)

    def test_payload_is_draft_on_each_platform(self):
        for platform in pipeline.PLATFORMS:
            item = buffer_draft.draft_input(platform, {"title": "Titre", "body": "Texte"}, "42",
                                            "https://host.example/video.mp4", ["https://www.rockstargames.com/VI"])
            self.assertTrue(item["saveToDraft"])
            self.assertNotIn("dueAt", item)
            if platform == "youtube":
                self.assertEqual(item["metadata"]["youtube"]["privacy"], "private")

    def test_exact_tiktok_identity_required(self):
        row = {"id": "id", "name": "@gtavieditfr", "service": "tiktok", "isDisconnected": False, "isLocked": False}
        self.assertEqual(buffer_draft.verified_channel([row], "id", "gtavieditfr", "tiktok"), row)
        with self.assertRaises(ValueError):
            buffer_draft.verified_channel([row], "id", "@other", "tiktok")

    def test_timeout_after_creation_does_not_create_duplicate(self):
        with sqlite3.connect(":memory:") as db:
            db.execute(buffer_draft.REGISTER)
            channel = {"id": "id"}
            asset = "https://host.example/video.mp4"
            payload = buffer_draft.draft_input("tiktok", {"body": "Text"}, "id", asset, [])
            with patch.object(buffer_draft, "existing_posts", return_value=[]):
                with patch.object(buffer_draft, "query", side_effect=TimeoutError) as query:
                    with self.assertRaises(TimeoutError):
                        buffer_draft.save_remote("token", db, "post", channel, payload)
                    with self.assertRaisesRegex(RuntimeError, "UNKNOWN_REMOTE"):
                        buffer_draft.save_remote("token", db, "post", channel, payload)
                    self.assertEqual(query.call_count, 1)
            existing = {"id": "provider-id", "text": "Text", "status": "draft", "assets": [{"source": asset}]}
            with patch.object(buffer_draft, "existing_posts", return_value=[existing]):
                with patch.object(buffer_draft, "query") as query:
                    self.assertEqual(buffer_draft.save_remote("token", db, "post", channel, payload), existing)
                    query.assert_not_called()

    def test_metrics_keeps_unknown_and_zero_distinct(self):
        output = io.StringIO()
        csv.writer(output).writerows([pipeline.METRICS_FIELDS, [
            "tiktok", "fixture", "news", NOW.isoformat(), (NOW + timedelta(hours=24)).isoformat(), "24",
            "0", "", "", "", "", "", "", "synthetic",
        ]])
        result = metrics.summarize(io.StringIO(output.getvalue()), synthetic=True)
        self.assertEqual(result["groups"][0]["metrics"]["views"], {"n": 1, "median": 0})
        self.assertEqual(result["groups"][0]["metrics"]["likes"], {"n": 0, "median": None})
        with self.assertRaises(ValueError):
            metrics.summarize(io.StringIO(output.getvalue()))


if __name__ == "__main__":
    unittest.main()
