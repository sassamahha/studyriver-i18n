#!/usr/bin/env python3
"""
RSS queue → GPT 翻訳 → アイキャッチ複製 → WP 投稿（10言語）
"""

from __future__ import annotations
import json, os, pathlib, re, sys, requests
from typing import Dict, List
from openai import OpenAI
from slugify import slugify

# ──────────────────────────
# 自作モジュール
# ──────────────────────────
SCRIPTS = pathlib.Path(__file__).resolve().parent
sys.path.append(str(SCRIPTS))
from utils import logger                  # noqa: E402
from upload_media import upload_image     # noqa: E402
from post_to_wp import create_post        # noqa: E402

# ──────────────────────────
# GPT / 共通定義
# ──────────────────────────
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
QUEUE_FILE = pathlib.Path("data/rss_queue.json")
if not QUEUE_FILE.exists():
    logger.info("queue empty – nothing to do")
    sys.exit(0)

# 投稿対象言語
LANGS = ["en","es","zhhans","zhhant","pt","id","fr","it","de",
    "ru","tr","ar","ko","th","vi","pl","fa","hi","sw","uk","sr","hu"]

# GPT に渡す正式名称マップ
LANG_NAME = {
    "en": "English",
    "es": "Spanish",
    "zhhans": "Simplified Chinese",
    "zhhant": "Traditional Chinese",
    "pt": "Portuguese",
    "id": "Indonesian",
    "fr": "French",
    "it": "Italian",
    "de": "German",
    "ru": "Russian",
    "tr": "Turkish",
    "ar": "Arabic",
    "ko": "Korean",
    "th": "Thai",
    "vi": "Vietnamese",
    "pl": "Polish",
    "fa": "Persian(Farsi)",
    "hi": "Hindi",
    "sw": "Swahili",
    "sr": "Serbian",
    "hu": "Hungarian",
}

_JSON = re.compile(r"\{[\s\S]+?\}")

def safe_json(txt: str) -> Dict[str,str]:
    m = _JSON.search(txt)
    if not m:
        raise ValueError("JSON not found")
    return json.loads(m.group(0))

# ──────────────────────────
# メイン処理
# ──────────────────────────
queue: List[Dict] = json.loads(QUEUE_FILE.read_text())

for item in queue:
    ja_id = item["post_id"]

    # 元記事取得
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

    # カテゴリ / タグ（無い場合は空）
    embed   = jp.get("_embedded", {})
    term    = embed.get("wp:term", [[], []])
    cat_ids = [c["id"] for c in term[0]]
    tag_ids = [t["id"] for t in term[1]]

# ───────── 翻訳ループ ─────────
for lang in LANGS:
    lang_full = LANG_NAME.get(lang, lang)
    logger.info(f"[{lang}] translating id={ja_id}")

    base_prompt = {
        "role": "user",
        "content": (
            'Return ONLY valid JSON like '
            '{"title":...,"content":...,"excerpt":...} translating the '
            f'article below to **{lang_full}**. Keep original HTML tags.\n---\n{body}'
        ),
    }

    # ─── 1st try ───
    try:
        rsp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[base_prompt],
            timeout=45,
        )
        tr = safe_json(rsp.choices[0].message.content)

    # ─── retry: 強制 JSON モード ───
    except Exception as first_err:
        logger.warning(f"parse fail ({lang}) – retry JSON mode: {first_err}")
        try:
            rsp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[base_prompt],
                response_format={"type": "json_object"},
                timeout=45,
            )
            tr = json.loads(rsp.choices[0].message.content)   # safe_json でなく直接 OK
        except Exception as second_err:
            logger.error(f"giving up ({lang}) – still invalid JSON: {second_err}")
            continue   # → 次の言語へ

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
