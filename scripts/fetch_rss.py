#!/usr/bin/env python3
"""日本語 WP から RSS を取得し、新規記事 ID をキュー化する"""
import os, feedparser, pathlib, json, sys, re

# --- utils 読み込み ---
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from utils import load_processed, save_processed, logger

WP_RSS_JP   = os.getenv("WP_RSS_JP", "https://studyriver.jp/feed")
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", 5))
QUEUE_FILE   = pathlib.Path("data/rss_queue.json")

processed = set(load_processed())
new_items = []

def extract_post_id(entry) -> int | None:
    """
    1. ?p=12345 型
    2. .../2025/05/12345/ 型
    のどちらかから post_id を整数で返す。取れなければ None。
    """
    candidates = [getattr(entry, "id", ""), getattr(entry, "link", "")]
    for url in candidates:
        # ?p=12345
        m = re.search(r"[?&]p=(\\d+)", url)
        if m:
            return int(m.group(1))
        # .../12345/ (末尾 or 末尾+スラッシュ)
        m = re.search(r"/(\\d{2,})/?$", url)
        if m:
            return int(m.group(1))
    return None

feed = feedparser.parse(WP_RSS_JP)

for entry in feed.entries[:MAX_ARTICLES]:
    post_id = extract_post_id(entry)
    if post_id and post_id not in processed:
        new_items.append(
            {
                "post_id": post_id,
                "title": entry.title,
                "link": entry.link,
                "published": entry.published,
            }
        )
        processed.add(post_id)

if new_items:
    logger.info(f"Queued {len(new_items)} new items → {QUEUE_FILE}")
    QUEUE_FILE.write_text(json.dumps(new_items, ensure_ascii=False, indent=2))
    save_processed(list(processed))
else:
    logger.info("No new items found.")
