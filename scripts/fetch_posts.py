#!/usr/bin/env python3
"""JP WordPress REST API から最新 N 件を取ってキュー化"""

import os, pathlib, json, requests, sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from utils import load_processed, save_processed, logger

WP_URL_JP    = os.getenv("WP_URL_JP", "https://studyriver.jp")
MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", 5))
QUEUE_FILE   = pathlib.Path("data/rss_queue.json")

API = f"{WP_URL_JP}/wp-json/wp/v2/posts"
PARAMS = {"per_page": MAX_ARTICLES, "_fields": "id,title,link,date"}

def main():
    processed = set(load_processed())
    new_items = []

    resp = requests.get(API, params=PARAMS, timeout=20)
    resp.raise_for_status()

    for post in resp.json():
        pid = post["id"]
        if pid not in processed:
            new_items.append({
                "post_id":   pid,
                "title":     post["title"]["rendered"],
                "link":      post["link"],
                "published": post["date"],
            })
            processed.add(pid)

    if new_items:
        logger.info(f"Queued {len(new_items)} items → {QUEUE_FILE}")
        QUEUE_FILE.write_text(json.dumps(new_items, ensure_ascii=False, indent=2))
        save_processed(sorted(processed))
    else:
        logger.info("No new items found.")

if __name__ == "__main__":
    main()
