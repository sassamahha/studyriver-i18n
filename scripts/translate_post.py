#!/usr/bin/env python3
"""
RSS queue → GPT 翻訳 → アイキャッチ複製 → WP 投稿（10言語）
"""

from __future__ import annotations
import json, os, pathlib, re, sys, requests
from typing import Dict, List
from openai import OpenAI
from slugify import slugify

# 自作モジュール
SCRIPTS = pathlib.Path(__file__).resolve().parent
sys.path.append(str(SCRIPTS))
from utils import logger              # noqa: E402
from upload_media import upload_image # noqa: E402
from post_to_wp import create_post    # noqa: E402

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
QUEUE_FILE = pathlib.Path("data/rss_queue.json")
if not QUEUE_FILE.exists():
    logger.info("queue empty – nothing to do"); sys.exit(0)

LANGS = ["en","es","zhhans","zhhant","pt","id","fr","it","de"]
_JSON = re.compile(r"\{[\s\S]+?\}")

def safe_json(txt: str) -> Dict[str,str]:
    m = _JSON.search(txt)
    if not m:
        raise ValueError("JSON not found")
    return json.loads(m.group(0))

queue: List[Dict] = json.loads(QUEUE_FILE.read_text())

for item in queue:
    ja_id = item["post_id"]
    jp = requests.get(
        f"https://studyriver.jp/wp-json/wp/v2/posts/{ja_id}?_embed"
    ).json()
    body = jp["content"]["rendered"]

    # アイキャッチ URL
    feat_src = None
    if jp.get("featured_media"):
        feat_src = requests.get(
            f"https://studyriver.jp/wp-json/wp/v2/media/{jp['featured_media']}"
        ).json().get("source_url")

    # カテゴリ / タグ（無い場合は空リスト）
    embed = jp.get("_embedded", {})
    term   = embed.get("wp:term", [[], []])
    cat_ids = [c["id"] for c in term[0]]
    tag_ids = [t["id"] for t in term[1]]

    for lang in LANGS:
        logger.info(f"[{lang}] translating id={ja_id}")

        prompt = {
            "role": "user",
            "content": (
                f'Return ONLY valid JSON like '
                f'{{"title":...,"content":...,"excerpt":...}} translating to {lang}. '
                f'Keep HTML tags.\n---\n{body}'
            ),
        }
        rsp = client.chat.completions.create(model="gpt-4o-mini", messages=[prompt])
        try:
            tr = safe_json(rsp.choices[0].message.content)
        except Exception as e:
            logger.error(f"JSON parse error ({lang}): {e}"); continue

        media_id = upload_image(feat_src) if feat_src else None

        payload = {
            "title": tr["title"],
            "content": tr["content"],
            "excerpt": tr["excerpt"],
            "slug": slugify(tr["title"]),
            "featured_media": media_id,
            "categories": cat_ids,
            "tags": tag_ids,
            "status": "publish",
        }

        try:
            new_id, link = create_post(payload, lang=lang, ja_id=ja_id)
            logger.info(f"✓ {lang} => {link}")
        except Exception as e:
            logger.error(f"WP error ({lang}): {e}")

logger.info("finished queue; removing file")
QUEUE_FILE.unlink(missing_ok=True)
