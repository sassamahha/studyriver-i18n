#!/usr/bin/env python3
"""共通ユーティリティ"""

import json, logging, os, base64, pathlib
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
ROOT      = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR  = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

PROCESSED_FILE     = DATA_DIR / "processed.json"
CATEGORY_MAP_FILE  = DATA_DIR / "category_mapping.json"   # ← data/ 配置に合わせて修正
TAG_MAP_FILE       = DATA_DIR / "tag_mapping.json"

# ==============================================================
# 既読記事 ID キャッシュ
# ==============================================================

def load_processed() -> List[int]:
    """processed.json から ID 配列を取得。無ければ空リスト。"""
    if PROCESSED_FILE.exists():
        try:
            return json.loads(PROCESSED_FILE.read_text()).get("processed", [])
        except json.JSONDecodeError:
            logger.warning("processed.json is malformed – starting fresh.")
    return []

def save_processed(ids: List[int]) -> None:
    """ID 配列を processed.json に保存（ソート付き）。"""
    PROCESSED_FILE.write_text(
        json.dumps({"processed": sorted(ids)}, ensure_ascii=False, indent=2)
    )

# ==============================================================
# カテゴリ／タグ名 → EN-WP 側 ID 取得
# ==============================================================

def load_mapping() -> Dict[str, Dict[str, int]]:
    """
    {
      "categories": {"未来教育": 42, ...},
      "tags":       {"生成AI":  99, ...}
    }
    """
    mapping = {"categories": {}, "tags": {}}

    if CATEGORY_MAP_FILE.exists():
        mapping["categories"] = json.loads(CATEGORY_MAP_FILE.read_text())

    if TAG_MAP_FILE.exists():
        mapping["tags"] = json.loads(TAG_MAP_FILE.read_text())

    return mapping

# ==============================================================
# WP Basic 認証ヘッダー生成
# ==============================================================

def basic_auth(user: str, app_pass: str) -> Dict[str, str]:
    """user と Application Password から Basic 認証ヘッダーを作成。"""
    token = base64.b64encode(f"{user}:{app_pass}".encode()).decode()
    return {"Authorization": f"Basic {token}"}
