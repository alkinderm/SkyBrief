import json
import time
import datetime as dt
from typing import List, Dict, Any

import feedparser

# Edit/expand this list any time.
FEEDS = [
    {
        "name": "Rubin Observatory News",
        "type": "rss",
        "url": "https://rubinobservatory.org/rss.xml",
        "tags": ["rubin", "lsst", "survey"]
    },
    {
        "name": "NOIRLab News",
        "type": "rss",
        "url": "https://noirlab.edu/public/news/feed/",
        "tags": ["noirlab", "ctio", "gemini", "astro"]
    },
    {
        "name": "Chandra Press Releases",
        "type": "rss",
        "url": "https://chandra.harvard.edu/rss/press.xml",
        "tags": ["chandra", "xray"]
    },
    {
        "name": "ESA/Hubble News",
        "type": "rss",
        "url": "https://esahubble.org/feed/news/",
        "tags": ["hubble", "esa"]
    },
    {
        "name": "NASA APOD",
        "type": "rss",
        "url": "https://apod.nasa.gov/apod.rss",
        "tags": ["apod", "nasa"]
    }
]

MAX_ITEMS_PER_FEED = 6
MAX_TOTAL_ITEMS = 40

def to_iso8601(struct_time) -> str:
    # feedparser returns time.struct_time sometimes
    return dt.datetime.fromtimestamp(time.mktime(struct_time), tz=dt.timezone.utc).isoformat().replace("+00:00", "Z")

def parse_entry(entry) -> Dict[str, Any]:
    title = getattr(entry, "title", "").strip()
    link = getattr(entry, "link", "").strip()
    summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
    summary = " ".join(summary.split()).strip()

    published = None
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        published = to_iso8601(entry.published_parsed)
    elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
        published = to_iso8601(entry.updated_parsed)

    return {
        "title": title,
        "summary": summary[:320] + ("…" if len(summary) > 320 else ""),
        "published_at": published or None,
        "url": link
    }

def main():
    items: List[Dict[str, Any]] = []
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    for feed in FEEDS:
        parsed = feedparser.parse(feed["url"])
        entries = getattr(parsed, "entries", [])[:MAX_ITEMS_PER_FEED]

        for e in entries:
            it = parse_entry(e)
            if not it["title"] and not it["url"]:
                continue
            it["tags"] = list(dict.fromkeys(feed.get("tags", []) + []))  # dedupe, preserve order
            it["source"] = {"name": feed["name"], "type": feed["type"], "url": feed["url"]}
            items.append(it)

    # Sort newest-first; None dates go last
    def sort_key(x):
        return x["published_at"] or "0000-01-01T00:00:00Z"
    items.sort(key=sort_key, reverse=True)

    # Trim
    items = items[:MAX_TOTAL_ITEMS]

    out = {
        "project": "SkyBrief",
        "generated_at": now,
        "items": items
    }

    with open("data/update.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote data/update.json with {len(items)} items.")

if __name__ == "__main__":
    main()
