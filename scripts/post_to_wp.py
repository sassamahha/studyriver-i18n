#!/usr/bin/env python3
"""
WordPress REST (Polylang) 投稿ユーティリティ

create_post(payload, lang=…, ja_id=…) を呼び出すと
  1. lang 用サブディレクトリ (/en/, /es/…) に投稿
  2. translations={ja: ja_id} で日本語記事とひも付け
  3. 成功したら公開先 URL と新記事 ID を返す
"""

from __future__ import annotations
import base64
import json
import os
from typing import Dict, Tuple

import requests

# ──────────────────────────
# 環境変数
# ──────────────────────────
WP_URL = os.environ["WP_URL"].rstrip("/")               # https://studyriver.jp/wp-json/wp/v2
AUTH   = base64.b64encode(
    f"{os.environ['WP_USER']}:{os.environ['WP_PASS']}".encode()
).decode()

HEADERS = {
    "Authorization": f"Basic {AUTH}",
    "Content-Type": "application/json",
}

# ──────────────────────────
# Public API
# ──────────────────────────
def create_post(payload: Dict, *, lang: str, ja_id: int) -> Tuple[int, str]:
    """
    payload : WP post JSON (title, content, slug, …)
    lang    : en / es / zhhans / …
    ja_id   : 元記事 (日本語) の Post ID
    return  : (new_id, link)
    """
    url  = f"{WP_URL}/posts?lang={lang}"
    data = payload | {"translations": {"ja": ja_id}}

    r = requests.post(url, headers=HEADERS, data=json.dumps(data), timeout=15)
    r.raise_for_status()

    js  = r.json()
    return js["id"], js.get("link")  # (new_id, permalink)

