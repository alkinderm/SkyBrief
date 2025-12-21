import json
import os
from datetime import datetime, timezone
from dateutil import tz
import feedparser

PACIFIC = tz.gettz("America/Los_Angeles")

FEEDS = [
    {"name": "arXiv astro-ph (new)", "kind": "rss", "url": "https://rss.arxiv.org/rss/astro-ph"},
    {"name": "ESA/Hubble News", "kind": "rss", "url": "https://esahubble.org/feeds/news/"}
]

STATIC_SOURCES = [
    {"name": "Rubin Observatory News", "kind": "web/news", "url": "https://rubinobservatory.org/news"},
    {"name": "ESO Press Releases", "kind": "web/press", "url": "https://www.eso.org/public/news/"},
    {"name": "NASA APOD", "kind": "web/daily", "url": "https://apod.nasa.gov/apod/astropix.html"}
]

def parse_dt(entry):
    t = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not t:
        return None
    return datetime(*t[:6], tzinfo=timezone.utc)

def main():
    now_utc = datetime.now(timezone.utc)
    now_pacific = now_utc.astimezone(PACIFIC)
    night_of = now_pacific.strftime("%Y-%m-%d")

    items = []

    for f in FEEDS:
        feed = feedparser.parse(f["url"])
        for e in feed.entries[:6]:
            dt = parse_dt(e)
            items.append({
                "title": (getattr(e, "title", "") or "").strip()[:140],
                "summary": (getattr(e, "summary", "") or "").replace("\n", " ").strip()[:240],
                "source": f["name"],
                "published_at": dt.astimezone(PACIFIC).isoformat() if dt else None,
                "link": getattr(e, "link", ""),
                "tags": ["feed"]
            })

    items.sort(key=lambda x: x["published_at"] or "", reverse=True)
    items = items[:10]

    update = {
        "brief_id": f"SKYBRIEF-{night_of}",
        "headline": "Tonight’s SkyBrief: top open updates across the sky",
        "night_of": night_of,
        "window_local": "Nightly around 02:30 America/Los_Angeles",
        "generated_at": now_pacific.isoformat(),
        "generator": "github-actions + feedparser",
        "sources": STATIC_SOURCES + FEEDS,
        "items": items
    }

    os.makedirs("data", exist_ok=True)
    with open("data/update.json", "w", encoding="utf-8") as f:
        json.dump(update, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
