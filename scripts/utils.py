#!/usr/bin/env python3
"""共通ユーティリティ（fetch / translate / post スクリプトで共有）"""

from __future__ import annotations

import base64
import json
import logging
import os
import pathlib
import re
import unicodedata
from typing import Dict, List

# ──────────────────────────
# ロガー
# ──────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("studyriver-i18n")

# ──────────────────────────
# パス設定
# ──────────────────────────
ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

PROCESSED_FILE     = DATA_DIR / "processed.json"
CATEGORY_MAP_FILE  = DATA_DIR / "category_mapping.json"
TAG_MAP_FILE       = DATA_DIR / "tag_mapping.json"

# ==============================================================
# slug 生成ユーティリティ（Polylang 用）
# ==============================================================

def _basic_slug(text: str) -> str:
    """日本語かな漢字混在でも読める slug を生成"""
    text = unicodedata.normalize("NFKD", text).lower()
    text = re.sub(r"[\u3000\s]+", "-", text)          # 全角スペース含む空白→-
    text = re.sub(r"[^0-9a-z\-ぁ-ん一-龥]+", "", text) # 記号削除
    return text.strip("-")[:80]

def slugify_for_lang(text: str, lang: str) -> str:
    """lang/slug 形式を返す"""
    return f"{lang}/{_basic_slug(text)}"

# ==============================================================
# 既読記事 ID キャッシュ
# ==============================================================

def load_processed() -> List[int]:
    if PROCESSED_FILE.exists():
        try:
            return json.loads(PROCESSED_FILE.read_text()).get("processed", [])
        except json.JSONDecodeError:
            logger.warning("processed.json is malformed – starting fresh.")
    return []

def save_processed(ids: List[int]) -> None:
    PROCESSED_FILE.write_text(
        json.dumps({"processed": sorted(ids)}, ensure_ascii=False, indent=2)
    )

# ==============================================================
# カテゴリ／タグ名 → WP ID 取得
# ==============================================================

def load_mapping() -> Dict[str, Dict[str, int]]:
    mapping: Dict[str, Dict[str, int]] = {"categories": {}, "tags": {}}

    if CATEGORY_MAP_FILE.exists():
        mapping["categories"] = json.loads(CATEGORY_MAP_FILE.read_text())

    if TAG_MAP_FILE.exists():
        mapping["tags"] = json.loads(TAG_MAP_FILE.read_text())

    return mapping

# ==============================================================
# WP Basic 認証ヘッダー生成
# ==============================================================

def basic_auth(user: str, app_pass: str) -> Dict[str, str]:
    token = base64.b64encode(f"{user}:{app_pass}".encode()).decode()
    return {"Authorization": f"Basic {token}"}
