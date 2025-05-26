#!/usr/bin/env python3
"""
最新 1 記事だけをキュー (data/rss_queue.json) に追加するスクリプト
--------------------------------------------------------------------
✓ RSS は使わず WordPress REST API で取得
✓ 既に処理済み ID はスキップ
✓ キューに追加したら processed.json を更新
"""

from __future__ import annotations
import json, os, pathlib, sys
import requests
# 自作 utils を読むための path 追加
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from utils import load_processed, save_processed, logger  # noqa: E402

# ──────────────────────────
# 設定
# ──────────────────────────
WP_URL_JP   = os.getenv("WP_URL_JP", "https://studyriver.jp")
QUEUE_FILE  = pathlib.Path("data/rss_queue.json")
QUEUE_FILE.parent.mkdir(exist_ok=True, parents=True)

API_ENDPOINT = f"{WP_URL_JP}/wp-json/wp/v2/posts"
PARAMS       = {"per_page": 1, "_fields": "id,title,link,date"}   # ← 最新 1 件固定

# ──────────────────────────
# 既読キャッシュ読み込み
# ──────────────────────────
processed: set[int] = set(load_processed())
queue: list[dict]   = []

# ──────────────────────────
# 投稿取得 & キュー生成
# ──────────────────────────
try:
    resp = requests.get(API_ENDPOINT, params=PARAMS, timeout=15)
    resp.raise_for_status()
    posts = resp.json()
except Exception as e:
    logger.error(f"API fetch failed: {e}")
    sys.exit(1)

if not posts:
    logger.info("No posts returned from API")
    sys.exit(0)

post = posts[0]                 # 最新 1 件だけ見る
pid  = post["id"]

if pid in processed:
    logger.info(f"Already processed id={pid}")
    sys.exit(0)

queue.append(
    {
        "post_id":   pid,
        "title":     post["title"]["rendered"],
        "link":      post["link"],
        "published": post["date"],
    }
)
processed.add(pid)

# ──────────────────────────
# 保存
# ──────────────────────────
QUEUE_FILE.write_text(json.dumps(queue, indent=2, ensure_ascii=False))
save_processed(sorted(processed))

logger.info(f"✓ queued 1 post (id={pid}) → {QUEUE_FILE}")
