#!/usr/bin/env python3
"""最新 1 記事だけ queue に追加"""

import json, pathlib, re
import feedparser
from utils import logger, load_processed, save_processed

RSS_URL = "https://studyriver.jp/feed/"
QUEUE   = pathlib.Path("data/rss_queue.json")

# 正規表現 例: https://studyriver.jp/?p=12345
_ID_RE  = re.compile(r"[?&]p=(\d+)")

def extract_post_id(entry) -> int | None:
    """feed entry から WP 投稿 ID を見つける"""
    # 1) WP が吐き出す拡張フィールド
    pid = entry.get("wp_post_id") or entry.get("post_id")
    if pid and pid.isdigit():
        return int(pid)

    # 2) permalink に ?p=123 が付く場合
    for url in (entry.get("id"), entry.get("link")):
        if not url:
            continue
        m = _ID_RE.search(url)
        if m:
            return int(m.group(1))
    return None   # 見つからない

# --------------------

feed = feedparser.parse(RSS_URL)
latest = feed.entries[:1]          # すでに pubDate 降順なので 1件

processed = set(load_processed())
queue = []

for ent in latest:
    pid = extract_post_id(ent)
    if not pid:
        logger.warning("post ID not found – skipped an entry")
        continue
    if pid in processed:
        logger.info(f"id={pid} already processed")
        continue
    queue.append({"post_id": pid})
    processed.add(pid)

if queue:
    QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2))
    save_processed(list(processed))
    logger.info(f"queued 1 item → {QUEUE}")
else:
    logger.info("no new item to queue")

