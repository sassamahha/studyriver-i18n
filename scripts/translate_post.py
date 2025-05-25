#!/usr/bin/env python3
"""
Queue → GPT 翻訳 → アイキャッチ UP → WordPress 投稿
Polylang Free＋サブディレクトリ構成（lang/slug）に対応
"""

from __future__ import annotations
import argparse
import json
import os
import pathlib
import re
import sys
from typing import Dict, List

import requests
from openai import OpenAI
from slugify import slugify  # pip install python-slugify

# ──────────────────────────
# 自作モジュールを読めるように sys.path 追加
# ──────────────────────────
SCRIPTS_DIR = pathlib.Path(__file__).resolve().parent
sys.path.append(str(SCRIPTS_DIR))

from utils import logger, load_mapping          # noqa: E402
from upload_media import upload_image           # noqa: E402
from post_to_wp import create_post              # noqa: E402

# ──────────────────────────
# 定数・初期化
# ──────────────────────────
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

QUEUE_FILE = pathlib.Path("data/rss_queue.json")
if not QUEUE_FILE.exists():
    logger.info("Queue empty – nothing to do")
    sys.exit(0)

# 変換先言語
parser = argparse.ArgumentParser()
parser.add_argument("--lang", default=os.getenv("TARGET_LANG", "en"))
LANG = parser.parse_args().lang.lower()

# 既存カテゴリ/タグとのマッピング
cat_map, tag_map = (
    load_mapping().get("categories", {}),
    load_mapping().get("tags", {}),
)

# ──────────────────────────
# GPT 出力 JSON を安全に切り出す
# ──────────────────────────
_JSON_RE = re.compile(r"\{[\s\S]+?\}")

def safe_json_block(text: str) -> Dict[str, str]:
    match = _JSON_RE.search(text)
    if not match:
        raise ValueError("JSON block not found in GPT output")
    return json.loads(match.group(0))

# ──────────────────────────
# メイン処理
# ──────────────────────────
queue: List[Dict] = json.loads(QUEUE_FILE.read_text())

for item in queue:
    pid = item["post_id"]
    logger.info(f"[{LANG}] translating post_id = {pid}")

    # 1) 元記事を取得
    jp = requests.get(
        f"https://studyriver.jp/wp-json/wp/v2/posts/{pid}?_embed"
    ).json()
    jp_content = jp["content"]["rendered"]

    # 2) GPT で翻訳
    prompt = {
        "role": "user",
        "content": (
            f"Return ONLY valid JSON like "
            f'{{\"title\":...,\"content\":...,\"excerpt\":...}} translating the '
            f"article below to {LANG}. Keep HTML tags.\n---\n{jp_content}"
        ),
    }
    rsp = client.chat.completions.create(
        model="gpt-4o-mini", messages=[prompt]
    )
    try:
        tr = safe_json_block(rsp.choices[0].message.content)
    except Exception as e:
        logger.error(f"JSON parse error: {e}")
        continue  # 次の記事へ

    # 3) アイキャッチ複製
    media_id = None
    if jp.get("featured_media"):
        src = requests.get(
            f"https://studyriver.jp/wp-json/wp/v2/media/{jp['featured_media']}"
        ).json()["source_url"]
        media_id = upload_image(src)

    # 4) カテゴリ／タグをマップ
    cats = [
        cat_map.get(t["name"])
        for t in jp["_embedded"]["wp:term"][0]
        if cat_map.get(t["name"])
    ]
    tags = [
        tag_map.get(t["name"])
        for t in jp["_embedded"]["wp:term"][1]
        if tag_map.get(t["name"])
    ]

    # 5) WP へ投稿
    payload = {
        "title": tr["title"],
        "content": tr["content"],
        "excerpt": tr["excerpt"],
        "slug": slugify(tr["title"]),          # lang/ はパーマリンク側が自動付与
        "featured_media": media_id,
        "categories": cats,
        "tags": tags,
        "status": "publish",
    }

    try:
        post_id = create_post(payload, lang=LANG, ja_id=pid)
        logger.info(f"✓ published {LANG} id={post_id}")
    except Exception as e:
        logger.error(f"WP post error: {e}")

logger.info("finished queue; removing file")
QUEUE_FILE.unlink(missing_ok=True)
