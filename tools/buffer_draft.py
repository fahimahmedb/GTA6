"""Discover Buffer channels or create one explicitly authorized video draft."""

import argparse
import hashlib
import json
import os
import socket
import sqlite3
from ipaddress import ip_address
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pipeline import OUTPUT, SCHEMA, catalog, eligibility, prepare_pack, refresh, utcnow
from render_seeds import BRAND_PATH, PLATFORMS, ROOT

API = "https://api.buffer.com"
POST_FIELDS = "id channelId status text assets { source }"
REGISTER = """
CREATE TABLE IF NOT EXISTS buffer_drafts (
    content_id TEXT, channel_id TEXT, state TEXT NOT NULL, remote_id TEXT,
    PRIMARY KEY (content_id, channel_id)
)
"""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def query(key, graphql, **variables):
    request = Request(
        API, data=json.dumps({"query": graphql, "variables": variables}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    with build_opener(NoRedirect()).open(request, timeout=15) as response:
        body = json.load(response)
    if body.get("errors") or not body.get("data"):
        raise RuntimeError("Buffer GraphQL request failed")
    return body["data"]


def channels(key):
    organizations = query(key, "{ account { organizations { id } } }")["account"]["organizations"]
    result = []
    for organization in organizations:
        result.extend(query(key, """
            query Channels($input: ChannelsInput!) {
                channels(input: $input) { id name service organizationId isDisconnected isLocked }
            }
        """, input={"organizationId": organization["id"]})["channels"])
    return [channel for channel in result if channel["service"] in PLATFORMS]


def verified_channel(available, channel_id, handle, platform):
    selected = next((channel for channel in available if channel["id"] == channel_id), None)
    if (
        not selected or selected["service"] != platform
        or selected["name"].lstrip("@").casefold() != handle.lstrip("@").casefold()
        or selected["isDisconnected"] or selected["isLocked"]
    ):
        raise ValueError("The exact connected channel and handle could not be verified")
    return selected


def draft_input(platform, caption, channel_id, asset_url, urls):
    text = caption["body"]
    asset = {"url": asset_url}
    metadata = {}
    if platform == "tiktok":
        asset["metadata"] = {"thumbnailOffset": 1000}
    elif platform == "instagram":
        asset["metadata"] = {"thumbnailOffset": 1000}
        metadata["instagram"] = {"type": "reel", "shouldShareToFeed": False}
    elif platform == "youtube":
        text += "\n\n" + "\n".join(dict.fromkeys(urls))
        metadata["youtube"] = {
            "title": caption["title"], "categoryId": "20", "madeForKids": False,
            "privacy": "private", "notifySubscribers": False,
        }
    else:
        raise ValueError("Unsupported destination")
    return {
        "channelId": channel_id, "text": text, "assets": [{"video": asset}],
        "schedulingType": "automatic", "mode": "addToQueue", "needsApproval": False,
        "saveToDraft": True, "metadata": metadata, "aiAssisted": True,
    }


def verify_asset(url, digest, expected_size):
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username is not None or parts.password is not None:
        raise ValueError("Expected a direct HTTPS video URL")
    addresses = socket.getaddrinfo(parts.hostname, parts.port or 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ip_address(addr[4][0]).is_global for addr in addresses):
        raise ValueError("Video host is not publicly reachable")
    with build_opener(NoRedirect()).open(url, timeout=15) as response:
        if response.headers.get_content_type() != "video/mp4":
            raise ValueError("Remote file is not served as video/mp4")
        data = response.read(expected_size + 1)
    if len(data) != expected_size or hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("Hosted media differs from the rendered file")


def existing_posts(key, channel):
    arguments = {"organizationId": channel["organizationId"], "filter": {"channelIds": [channel["id"]]}}
    cursor = None
    while True:
        page = query(key, f"""
            query Posts($input: PostsInput!, $after: String) {{
                posts(first: 25, after: $after, input: $input) {{
                    edges {{ node {{ {POST_FIELDS} }} }} pageInfo {{ hasNextPage endCursor }}
                }}
            }}
        """, input=arguments, after=cursor)["posts"]
        yield from (edge["node"] for edge in page["edges"])
        info = page["pageInfo"]
        if not info["hasNextPage"]:
            break
        if not info["endCursor"] or info["endCursor"] == cursor:
            raise RuntimeError("Buffer pagination could not be reconciled")
        cursor = info["endCursor"]


def save_remote(key, db, content_id, channel, payload):
    channel_id = channel["id"]
    record = db.execute(
        "SELECT state, remote_id FROM buffer_drafts WHERE content_id=? AND channel_id=?",
        (content_id, channel_id),
    ).fetchone()
    if record and record[1]:
        return reread(key, record[1], channel_id)
    same_text = [post for post in existing_posts(key, channel) if post["text"] == payload["text"]]
    expected_url = payload["assets"][0]["video"]["url"]
    if same_text:
        if len(same_text) != 1 or not any(a["source"] == expected_url for a in (same_text[0]["assets"] or [])):
            raise RuntimeError("Potential duplicate on Buffer. Reconcile its ID and media before retrying.")
        post = same_text[0]
        with db:
            db.execute("""
                INSERT INTO buffer_drafts VALUES (?, ?, ?, ?)
                ON CONFLICT (content_id, channel_id) DO UPDATE SET state=excluded.state, remote_id=excluded.remote_id
            """, (content_id, channel_id, post["status"], post["id"]))
        return post
    if record:
        raise RuntimeError("UNKNOWN_REMOTE: previous attempt has no receipt. No automatic retry.")
    with db:
        reserved = db.execute(
            "INSERT OR IGNORE INTO buffer_drafts VALUES (?, ?, 'UNKNOWN_REMOTE', NULL)",
            (content_id, channel_id),
        ).rowcount
    if not reserved:
        raise RuntimeError("Another execution reserved this draft")
    result = query(key, f"""
        mutation Draft($input: CreatePostInput!) {{
            createPost(input: $input) {{
                ... on PostActionSuccess {{ post {{ {POST_FIELDS} }} }}
                ... on MutationError {{ message }}
            }}
        }}
    """, input=payload)["createPost"]
    post = result.get("post")
    if not post:
        raise RuntimeError("No Buffer receipt. Reconcile the queue before retrying.")
    with db:
        db.execute(
            "UPDATE buffer_drafts SET state=?, remote_id=? WHERE content_id=? AND channel_id=?",
            (post["status"], post["id"], content_id, channel_id),
        )
    observed = reread(key, post["id"], channel_id)
    if observed["status"] != "draft":
        raise RuntimeError("Buffer returned a status other than draft. Verify before any further action.")
    return observed


def reread(key, remote_id, channel_id):
    post = query(key, f"""
        query ReadPost($input: PostInput!) {{ post(input: $input) {{ {POST_FIELDS} }} }}
    """, input={"id": remote_id})["post"]
    if not post or post["id"] != remote_id or post["channelId"] != channel_id:
        raise RuntimeError("The Buffer receipt could not be verified")
    return post


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("channels")
    draft = sub.add_parser("draft")
    for name in ("content", "channel", "handle", "asset-url"):
        draft.add_argument(f"--{name}", required=True)
    draft.add_argument("--platform", choices=PLATFORMS, required=True)
    draft.add_argument("--confirm-draft", action="store_true", required=True)
    args = parser.parse_args()
    key = os.environ.get("BUFFER_API_KEY")
    if not key:
        parser.exit(2, "BLOCK: BUFFER_API_KEY unavailable. Use the local pack in native Studio.\n")
    if args.command == "channels":
        print(json.dumps(channels(key), indent=2))
        return
    try:
        channel = verified_channel(channels(key), args.channel, args.handle, args.platform)
        facts, posts = catalog()
        post = next((item for item in posts if item["id"] == args.content), None)
        if not post:
            raise ValueError("Invalid content ID")
        OUTPUT.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(OUTPUT / "state.sqlite3") as db:
            db.executescript(SCHEMA)
            db.execute(REGISTER)
            snapshot = refresh(facts, db, OUTPUT)
            state, reason, _ = eligibility(post, snapshot["facts"], utcnow())
            if state != "READY_LOCAL":
                raise ValueError(reason)
            renderer = hashlib.sha256((ROOT / "tools" / "render_seeds.py").read_bytes() + BRAND_PATH.read_bytes()).hexdigest()
            manifest = prepare_pack(post, facts, OUTPUT, renderer)
            media = OUTPUT / "packs" / args.content / "video.mp4"
            verify_asset(args.asset_url, manifest["sha256"], media.stat().st_size)
            urls = [url for fact_id in post["fact_ids"] for url in facts[fact_id]["sources"]]
            payload = draft_input(args.platform, post["captions"][args.platform], args.channel, args.asset_url, urls)
            observed = save_remote(key, db, args.content, channel, payload)
            print(json.dumps({field: observed[field] for field in ("id", "channelId", "status")}))
    except OSError as exc:
        parser.exit(1, f"Remote or local transport failed ({type(exc).__name__}).\n")
    except (ValueError, RuntimeError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
