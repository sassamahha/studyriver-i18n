#!/usr/bin/env python3
"""日本語 RSS を読み取り → 最新 1 記事だけ data/rss_queue.json へ"""

import feedparser, pathlib, json, time
from utils import logger, load_processed, save_processed

RSS_URL  = "https://studyriver.jp/feed/"
QUEUE    = pathlib.Path("data/rss_queue.json")

parsed   = feedparser.parse(RSS_URL)
processed_ids = set(load_processed())

# ── pubDate 降順で並び替えして先頭 1 件だけ
items = sorted(parsed.entries, key=lambda e: e.published_parsed, reverse=True)[:1]

queue = []
for e in items:
    post_id = int(e.id.split("=")[-1])
    if post_id in processed_ids:
        logger.info(f"skip already processed id={post_id}")
        continue
    queue.append({"post_id": post_id})
    processed_ids.add(post_id)

if queue:
    QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2))
    save_processed(list(processed_ids))
    logger.info(f"queued 1 item → {QUEUE}")
else:
    logger.info("no new item")
