#!/usr/bin/env python3
"""WP REST API で最新記事を取得し、未処理 ID をキュー化"""
import os, pathlib, json, requests, sys
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from utils import load_processed, save_processed, logger

WP_URL_JP    = os.getenv("WP_URL_JP", "https://studyriver.jp")
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", 5))
QUEUE_FILE   = pathlib.Path("data/rss_queue.json")

API_ENDPOINT = f"{WP_URL_JP}/wp-json/wp/v2/posts"
PARAMS       = {
    "per_page": MAX_ARTICLES,
    "_fields": "id,title,link,date"
}

processed = set(load_processed())
new_items = []

resp = requests.get(API_ENDPOINT, params=PARAMS, timeout=20)
resp.raise_for_status()

for post in resp.json():
    post_id = post["id"]
    if post_id not in processed:
        new_items.append({
            "post_id":   post_id,
            "title":     post["title"]["rendered"],
            "link":      post["link"],
            "published": post["date"],
        })
        processed.add(post_id)

if new_items:
    logger.info(f"Queued {len(new_items)} items → {QUEUE_FILE}")
    QUEUE_FILE.write_text(json.dumps(new_items, ensure_ascii=False, indent=2))
    save_processed(sorted(processed))
else:
    logger.info("No new items found.")
