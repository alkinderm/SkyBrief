import json
import os
from datetime import datetime, timezone
import feedparser

# -----------------------------
# Configuration
# -----------------------------

FEEDS = [
    {
        "name": "arXiv astro-ph (recent)",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/astro-ph",
        "tags": ["arxiv", "astro-ph"]
    },
    {
        "name": "ESA / Hubble News",
        "type": "rss",
        "url": "https://esahubble.org/feeds/news/",
        "tags": ["esa", "hubble"]
    },
    {
        "name": "NOIRLab News",
        "type": "rss",
        "url": "https://noirlab.edu/public/news/feed/",
        "tags": ["noirlab"]
    }
]

MAX_ITEMS_PER_FEED = 6
MAX_TOTAL_ITEMS = 20


# -----------------------------
# Helpers
# -----------------------------

def parse_time(entry):
    """Return ISO8601 string if feedparser gives us a time."""
    t = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not t:
        return None
    return datetime(*t[:6], tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def clean_text(s, limit=None):
    if not s:
        return ""
    s = " ".join(s.replace("\n", " ").split())
    if limit and len(s) > limit:
        return s[:limit].rstrip() + "…"
    return s


# -----------------------------
# Main
# -----------------------------

def main():
    items = []

    for feed in FEEDS:
        parsed = feedparser.parse(feed["url"])
        entries = parsed.entries[:MAX_ITEMS_PER_FEED]

        for e in entries:
            title = clean_text(getattr(e, "title", ""), 140)
            summary = clean_text(
                getattr(e, "summary", "") or getattr(e, "description", ""),
                280
            )
            link = getattr(e, "link", "")
            published = parse_time(e)

            if not title and not link:
                continue

            items.append({
                "title": title or "Untitled update",
                "summary": summary,
                "published_at": published,
                "url": link,
                "tags": feed.get("tags", []),
                "source": {
                    "name": feed["name"],
                    "type": feed["type"],
                    "url": feed["url"]
                }
            })

    # Sort newest first (None dates go last)
    items.sort(
        key=lambda x: x["published_at"] or "0000-01-01T00:00:00Z",
        reverse=True
    )

    items = items[:MAX_TOTAL_ITEMS]

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    output = {
        "project": "SkyBrief",
        "generated_at": now,
        "items": items
    }

    os.makedirs("data", exist_ok=True)

    with open("data/update.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"SkyBrief update written with {len(items)} items.")


if __name__ == "__main__":
    main()
