"""GTA VI source refresh, local editorial queue and downloadable post packs."""

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import subprocess
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from zoneinfo import ZoneInfo

from render_seeds import BRAND_PATH, PLATFORMS, ROOT, build_pack
from verified_sources import collect, discover, verify

PARIS = ZoneInfo("Europe/Paris")
OUTPUT = ROOT / "output" / "pipeline"
METRICS_FIELDS = (
    "platform", "native_id", "pillar", "published_at", "captured_at", "window_hours",
    "views", "likes", "comments", "shares", "saves", "retention_percent", "follower_count", "source",
)
SCHEMA = """
CREATE TABLE IF NOT EXISTS fact_versions (
    id TEXT, version TEXT, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL,
    record TEXT NOT NULL, PRIMARY KEY (id, version)
);
CREATE TABLE IF NOT EXISTS discovered (
    url TEXT PRIMARY KEY, title TEXT NOT NULL, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS local_queue (
    id TEXT, platform TEXT, revision TEXT, source_until TEXT,
    due_utc TEXT, state TEXT NOT NULL, reason TEXT,
    PRIMARY KEY (id, platform)
);
"""


def utcnow():
    return datetime.now(timezone.utc)


def parse_time(value):
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError("An explicit UTC offset is required")
    return result.astimezone(timezone.utc)


def to_sha(data):
    body = json.dumps(data, ensure_ascii=False, sort_keys=True).encode()
    return hashlib.sha256(body).hexdigest()


def put_json(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as output:
        json.dump(content, output, ensure_ascii=False, indent=2)
        output.write("\n")
    Path(output.name).replace(path)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def reviewed_master(manifest):
    """The editorial review identifies the exact cut and its visual and rights evidence."""
    review = manifest.get("editorial_review")
    return bool(
        manifest.get("state") == "APPROVED"
        and isinstance(review, dict)
        and manifest.get("sha256")
        and review.get("sha256") == manifest["sha256"]
        and review.get("visual_evidence")
        and review.get("rights_reference")
    )


def catalog():
    facts, posts = {}, []
    for file in ("seed.json", "series.json"):
        edition = load_json(ROOT / "editorial" / file)
        if set(edition["facts"]) & set(facts):
            raise ValueError("Duplicate fact ID")
        facts.update(edition["facts"])
        posts.extend(edition["posts"])
    if len({post["id"] for post in posts}) != len(posts):
        raise ValueError("Duplicate post ID")
    return facts, posts


def refresh(facts, db, output):
    pages = collect()
    observed = utcnow().isoformat()
    evidence = verify(facts, pages)
    candidates = discover(pages)
    with db:
        for fact_id, record in evidence.items():
            version = to_sha({
                "claim": record["claim"], "status": record["status"],
                "urls": record["source_urls"],
                "source_fragments": {url: item["sha256"] for url, item in record["evidence"].items()},
            })
            db.execute("""
                INSERT INTO fact_versions VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (id, version) DO UPDATE SET last_seen=excluded.last_seen, record=excluded.record
            """, (fact_id, version, observed, observed, json.dumps(record, ensure_ascii=False)))
        for item in candidates:
            db.execute("""
                INSERT INTO discovered VALUES (?, ?, ?, ?)
                ON CONFLICT (url) DO UPDATE SET title=excluded.title, last_seen=excluded.last_seen
            """, (item["url"], item["title"], observed, observed))
    snapshot = {
        "observed_at_utc": observed, "facts": evidence, "discoveries": candidates,
        "pages": [{key: value for key, value in page.items() if key not in {"text", "links"}} for page in pages.values()],
    }
    put_json(output / "sources.json", snapshot)
    print(f"Sources: {sum(page.get('http_status') == 200 for page in pages.values())}/{len(pages)} HTTP 200, "
          f"{sum(row['status'] == 'confirmed' for row in evidence.values())}/{len(facts)} confirmed, "
          f"{len(candidates)} Newswire leads")
    return snapshot


def eligibility(post, evidence, now):
    if post.get("state") == "HOLD":
        return "BLOCK", post["reason"], None
    expiration = post.get("valid_until")
    if expiration and parse_time(expiration) <= now:
        return "EXPIRED", "L’échéance de ce sujet est passée.", expiration
    for fact_id in post["fact_ids"]:
        record = evidence.get(fact_id, {})
        if record.get("status") != "confirmed":
            return "BLOCK", f"Vérification source : {fact_id} ({record.get('status', 'missing')}).", None
    threshold = min(parse_time(evidence[fact_id]["valid_until"]) for fact_id in post["fact_ids"])
    if expiration:
        threshold = min(parse_time(expiration), threshold)
    if threshold <= now:
        return "BLOCK", "Les sources doivent être relues.", threshold.isoformat()
    return "READY_LOCAL", None, threshold.isoformat()


def prepare_pack(post, facts, output, renderer_version):
    post_id = post["id"]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", post_id):
        raise ValueError(f"Invalid post ID: {post_id}")
    pack = output / "packs" / post_id
    revision = to_sha({"post": post, "facts": {key: facts[key] for key in post["fact_ids"]}, "renderer": renderer_version})
    manifest_path = pack / "manifest.json"
    if manifest_path.is_file():
        manifest = load_json(manifest_path)
        needed = ["video.mp4", "subtitles.srt", "cover.jpg", *(f"{platform}.txt" for platform in PLATFORMS)]
        if manifest.get("revision") == revision and all((pack / filename).is_file() for filename in needed):
            if hashlib.sha256((pack / "video.mp4").read_bytes()).hexdigest() == manifest["sha256"]:
                return manifest
    build_pack(post, facts, pack.parent)
    manifest = load_json(manifest_path)
    subprocess.run([
        "ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", "1", "-i", str(pack / "video.mp4"),
        "-frames:v", "1", "-threads", "1", str(pack / "cover.jpg"),
    ], check=True)
    manifest["revision"] = revision
    put_json(manifest_path, manifest)
    return manifest


def proposed_slots(now, ids):
    local_now = now.astimezone(PARIS)
    start = local_now.date()
    cutoff = start + timedelta(days=6)
    proposals = []
    for index, post_id in enumerate(ids):
        day = start + timedelta(days=index)
        if day > cutoff:
            break
        slot = datetime.combine(day, time(19), PARIS)
        if slot <= local_now:
            slot = (local_now + timedelta(minutes=15)).replace(second=0, microsecond=0)
            if slot.date() != day:
                continue
        proposals.append((post_id, slot))
    return proposals


def plan(facts, posts, snapshot, db, output, now):
    renderer = hashlib.sha256((ROOT / "tools" / "render_seeds.py").read_bytes() + BRAND_PATH.read_bytes()).hexdigest()
    order = ("p01-heure-france", "p02-vice-city-leonida", "p03-jason-lucia", "p06-apercu-ps5",
             "p07-leonida-keys", "p14-trouver-info-officielle", "p08-ville-ou-exploration")
    # Retain catalog order for new subjects that are not yet in the sequence.
    rank = {post_id: index for index, post_id in enumerate(order)}
    entries = {}
    for post in sorted(posts, key=lambda item: rank.get(item["id"], len(rank))):
        state, reason, valid_until = eligibility(post, snapshot["facts"], now)
        manifest = prepare_pack(post, facts, output, renderer) if state == "READY_LOCAL" else {}
        if state == "READY_LOCAL" and not reviewed_master(manifest):
            state = "PREVIEW_ONLY"
            reason = "Montage de travail. Revue éditoriale et droits à établir sur le fichier final."
        entries[post["id"]] = {
            "state": state, "reason": reason, "source_until": valid_until,
            "expires_at": post.get("valid_until"), "revision": manifest.get("revision"),
            "sha256": manifest.get("sha256"), "pack": f"packs/{post['id']}" if manifest else None,
            "cover": post["cover"],
        }
    ready = [post_id for post_id, entry in entries.items() if entry["state"] == "READY_LOCAL"]
    proposals = dict(proposed_slots(now, ready))
    rows = []
    with db:
        for post_id, entry in entries.items():
            proposed = proposals.get(post_id)
            if proposed and entry["expires_at"] and proposed >= parse_time(entry["expires_at"]):
                proposed = None
            for platform in PLATFORMS:
                due_at = proposed.astimezone(timezone.utc).isoformat() if proposed else None
                state = entry["state"]
                reason = entry["reason"]
                if due_at and parse_time(due_at) >= parse_time(entry["source_until"]):
                    state, reason = "RECHECK", "Relire les sources avant ce créneau."
                db.execute("""
                    INSERT INTO local_queue VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (id, platform) DO UPDATE SET revision=excluded.revision,
                        source_until=excluded.source_until, due_utc=excluded.due_utc,
                        state=excluded.state, reason=excluded.reason
                """, (post_id, platform, entry["revision"], entry["source_until"], due_at, state, reason))
                rows.append({
                    "id": post_id, "platform": platform, "proposed_paris": proposed.isoformat() if proposed else None,
                    "proposed_utc": due_at, "state": state, "reason": reason,
                })
    queue = {"generated_at_utc": now.isoformat(), "mode": "LOCAL_ONLY", "posts": entries, "queue": rows}
    put_json(output / "queue.json", queue)
    first_day = now.astimezone(PARIS).date()
    with (output / "planning.csv").open("w", newline="", encoding="utf-8-sig") as out:
        writer = csv.DictWriter(out, fieldnames=("id", "platform", "proposed_paris", "proposed_utc", "state", "reason"))
        writer.writeheader()
        writer.writerows(rows)
        booked = {parse_time(row["proposed_utc"]).astimezone(PARIS).date() for row in rows if row["proposed_utc"]}
        for delta in range(7):
            day = first_day + timedelta(days=delta)
            if day not in booked:
                writer.writerow({"proposed_paris": day.isoformat(), "state": "EMPTY", "reason": "Aucun sujet prévu."})
    with (output / "metriques-vierge.csv").open("w", newline="", encoding="utf-8-sig") as file:
        csv.writer(file).writerow(METRICS_FIELDS)
    print(f"Local: {len(ready)} reviewed masters, {len(rows)} rows, {sum(row['state'] == 'RECHECK' for row in rows)} requiring recheck")
    return queue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "refresh", "plan"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    facts, posts = catalog()
    with sqlite3.connect(output / "state.sqlite3") as db:
        db.executescript(SCHEMA)
        if args.command in {"run", "refresh"}:
            snapshot = refresh(facts, db, output)
        else:
            snapshot = load_json(output / "sources.json")
        if args.command in {"run", "plan"}:
            plan(facts, posts, snapshot, db, output, utcnow())


if __name__ == "__main__":
    main()
