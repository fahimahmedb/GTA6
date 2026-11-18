"""Read primary GTA VI pages and check the factual claims used by the catalog."""

import hashlib
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen

GAME = "https://www.rockstargames.com/VI"
SUPPORT = (
    "https://support.rockstargames.com/articles/29jV3Cv2cCgvwM1XgtMO5o/"
    "grand-theft-auto-vi-regional-pre-load-and-release-times-on-playstation-5-and-xbox-series-x-or-s"
)
INVESTOR = "https://www.take2games.com/ir/news/take-two-interactive-software-inc-reports-results-fiscal-4"
PLAYSTATION = "https://www.playstation.com/en-us/games/grand-theft-auto-vi/"
LEONIDA = "https://www.rockstargames.com/VI/only-in-leonida"
HOSTS = {"www.rockstargames.com", "support.rockstargames.com", "www.take2games.com", "www.playstation.com"}
WATCH = (GAME, SUPPORT, INVESTOR, PLAYSTATION, LEONIDA)
CLAIMS = {
    "release-fr": {
        "hours": 2,
        "source_published_at": "2026-11-03",
        "facts": {
            SUPPORT: r"will release midnight local time on november 19, 2026.{0,115}playstation 5 and xbox series x\s*\|\s*s",
            GAME: r"coming\s+november 19, 2026",
        },
    },
    "vice-city": {"facts": {GAME: r"vice city, usa\. jason and lucia.{0,420}state of leonida"}},
    "duo": {"facts": {GAME: r"jason and lucia.{0,280}easy score.{0,230}conspiracy.{0,100}leonida"}},
    "extended-look": {"facts": {PLAYSTATION: r"captured entirely from in-game footage on playstation 5"}},
    "official-trailers": {"facts": {GAME: r"launch trailer.{0,330}trailer 2.{0,70}trailer 1"}},
    "leonida-keys": {
        "facts": {LEONIDA: r"jason duval.{0,680}he found himself in the keys"},
    },
    "regional-support": {
        "source_published_at": "2026-11-03",
        "facts": {SUPPORT: r"regional pre-load and release times.{0,140}playstation 5 and xbox series x"},
    },
}


def canonical(url):
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc not in HOSTS:
        raise ValueError("Unrecognized source URL")
    query = urlencode([
        (key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in {"pubdate", "trk", "_rsc"}
    ])
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/") or "/", query, ""))


class Document(HTMLParser):
    ignored = {"script", "style", "template", "noscript", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = []
        self.words = []
        self.links = []
        self.anchor = None

    def handle_starttag(self, tag, attrs):
        if tag in self.ignored:
            self.hidden.append(tag)
        elif not self.hidden and tag == "img":
            self.handle_data(dict(attrs).get("alt") or "")
        elif not self.hidden and tag == "a":
            href = dict(attrs).get("href")
            self.anchor = (href, []) if href else None

    def handle_endtag(self, tag):
        if self.hidden:
            if tag == self.hidden[-1]:
                self.hidden.pop()
        elif tag == "a" and self.anchor:
            href, words = self.anchor
            self.links.append((href, " ".join(words)))
            self.anchor = None

    def handle_data(self, value):
        words = " ".join(value.split())
        if words and not self.hidden:
            self.words.append(words)
            if self.anchor:
                self.anchor[1].append(words)


def fetch_page(url):
    request = Request(url, headers={"User-Agent": "GTA-VI-Edit-FR/1.0 (public-fact-check)"})
    with urlopen(request, timeout=10) as response:
        if response.headers.get_content_type() != "text/html":
            raise ValueError("Expected HTML")
        final = canonical(response.geturl())
        if urlsplit(final).hostname != urlsplit(url).hostname:
            raise ValueError("Unexpected source host")
        data = response.read(4_000_001)
        if len(data) > 4_000_000:
            raise ValueError("HTML exceeded collection limit")
        document = Document()
        document.feed(data.decode(response.headers.get_content_charset() or "utf-8", errors="replace"))
        body = " ".join(document.words)
        return {
            "url": final, "http_status": response.status, "bytes": len(data),
            "collected_at_utc": datetime.now(timezone.utc).isoformat(),
            "text": body, "links": document.links,
        }


def collect():
    def read(url):
        try:
            return fetch_page(url)
        except (OSError, ValueError) as exc:
            return {
                "url": url, "http_status": exc.code if isinstance(exc, HTTPError) else None,
                "collected_at_utc": datetime.now(timezone.utc).isoformat(), "error": type(exc).__name__,
            }

    with ThreadPoolExecutor(max_workers=5) as pool:
        return dict(zip(WATCH, pool.map(read, WATCH)))


def verify(facts, pages):
    verified = {}
    for fact_id, fact in facts.items():
        rule = CLAIMS.get(fact_id, {})
        patterns = rule.get("facts", {})
        evidence = {}
        for url, expression in patterns.items():
            page = pages.get(url, {})
            match = re.search(expression, page.get("text", ""), re.IGNORECASE)
            if match and page.get("http_status") == 200:
                evidence[url] = {
                    "sha256": hashlib.sha256(match.group().casefold().encode()).hexdigest(),
                    "read_at": page["collected_at_utc"],
                }
        status = "confirmed" if patterns and len(evidence) == len(patterns) else "unverified"
        if fact_id == "release-fr":
            dates = set()
            for url, expression in (
                (SUPPORT, r"will release midnight local time on ([a-z]+ \d{1,2}, \d{4})"),
                (GAME, r"coming\s+([a-z]+ \d{1,2}, \d{4})"),
            ):
                if pages.get(url, {}).get("http_status") == 200:
                    dates.update(
                        found.casefold()
                        for found in re.findall(expression, pages[url]["text"], re.IGNORECASE)
                    )
            if dates - {"november 19, 2026"}:
                status = "conflict"
        valid_until = None
        if status == "confirmed":
            earliest = min(datetime.fromisoformat(item["read_at"]) for item in evidence.values())
            valid_until = (earliest + timedelta(hours=rule.get("hours", 48))).isoformat()
        verified[fact_id] = {
            "claim": fact["claim"], "source_urls": list(dict.fromkeys(fact["sources"])),
            "source_published_at": rule.get("source_published_at"),
            "status": status, "valid_until": valid_until, "evidence": evidence,
        }
    return verified


def discover(pages):
    news = {}
    for page in pages.values():
        if page.get("http_status") != 200:
            continue
        for href, title in page["links"]:
            if not title:
                continue
            try:
                url = canonical(urljoin(page["url"], href))
            except ValueError:
                continue
            parsed = urlsplit(url)
            if parsed.hostname == "www.rockstargames.com" and re.fullmatch(
                r"/newswire/article/[a-z0-9]+(?:/[^/]+)?", parsed.path, re.IGNORECASE
            ):
                slug = parsed.path.split("/")[3].casefold()
                news.setdefault(slug, {"url": url, "title": title, "state": "discovered"})
    return list(news.values())
