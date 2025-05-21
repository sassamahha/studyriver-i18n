#!/usr/bin/env python3
"""日本語 WP の RSS から新着記事を抽出 → キュー化"""
import os, feedparser, pathlib, json, sys, re

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from utils import load_processed, save_processed, logger

WP_RSS_JP    = os.getenv("WP_RSS_JP", "https://studyriver.jp/feed")
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", 5))
QUEUE_FILE   = pathlib.Path("data/rss_queue.json")

processed = set(load_processed())
new_items = []

def extract_post_id(entry) -> int | None:
    """
    1) ?p=12345
    2) https://.../YYYY/MM/12345/ or .../12345
    のどちらかから post_id(int) を返す
    """
    for url in (getattr(entry, "id", ""), getattr(entry, "link", "")):
        if not url:
            continue
        m = re.search(r"[?&]p=(\\d+)", url)
        if m:
            return int(m.group(1))
        m = re.search(r"/(\\d{2,})/?$", url)
        if m:
            return int(m.group(1))
    return None

feed = feedparser.parse(WP_RSS_JP)

for entry in feed.entries[:MAX_ARTICLES]:
    post_id = extract_post_id(entry)
    if post_id and post_id not in processed:
        new_items.append({
            "post_id": post_id,
            "title": entry.title,
            "link":  entry.link,
            "published": entry.published,
        })
        processed.add(post_id)

if new_items:
    logger.info(f"Queued {len(new_items)} items → {QUEUE_FILE}")
    QUEUE_FILE.write_text(json.dumps(new_items, ensure_ascii=False, indent=2))
    save_processed(sorted(processed))
else:
    logger.info("No new items found.")
