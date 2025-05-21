#!/usr/bin/env python3
"""日本語 WP から RSS を取得し、新規記事 ID リストをキュー化する"""
import os, feedparser, pathlib, json
from utils import load_processed, save_processed, logger

WP_RSS_JP = os.getenv("WP_RSS_JP", "https://studyriver.jp/feed")
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", 5))
QUEUE_FILE = pathlib.Path("data/rss_queue.json")

processed = set(load_processed())

feed = feedparser.parse(WP_RSS_JP)
new_items = []

for entry in feed.entries[:MAX_ARTICLES]:
    post_id = int(entry.id.split("=")[-1])  # ?p=12345 形式を想定
    if post_id not in processed:
        new_items.append({
            "post_id": post_id,
            "title": entry.title,
            "link": entry.link,
            "published": entry.published,
        })
        processed.add(post_id)

if new_items:
    logger.info(f"Queued {len(new_items)} new items → {QUEUE_FILE}")
    QUEUE_FILE.write_text(json.dumps(new_items, ensure_ascii=False, indent=2))
    save_processed(list(processed))
else:
    logger.info("No new items found.")