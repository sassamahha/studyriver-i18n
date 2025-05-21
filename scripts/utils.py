# scripts/utils.py
import json, logging, os, base64, pathlib
from typing import Dict, List

# ---------- ロガー ----------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("studyriver-i18n")

# ---------- パス ----------
ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

PROCESSED_FILE      = DATA_DIR / "processed.json"
CATEGORY_MAP_FILE   = ROOT / "config" / "category_mapping.json"
TAG_MAP_FILE        = ROOT / "config" / "tag_mapping.json"

# ==============================================================
# 既読記事 ID のキャッシュ
# ==============================================================

def load_processed() -> List[int]:
    """
    processed.json から ID の配列を返す。
    無い or 壊れている場合は空リスト。
    """
    if PROCESSED_FILE.exists():
        try:
            return json.loads(PROCESSED_FILE.read_text()).get("processed", [])
        except json.JSONDecodeError:
            logger.warning("processed.json is malformed – starting fresh.")
    return []

def save_processed(ids: List[int]) -> None:
    """
    ID リストを processed.json に保存（整形付き）。
    """
    PROCESSED_FILE.write_text(
        json.dumps({"processed": sorted(ids)}, ensure_ascii=False, indent=2)
    )

# ==============================================================
# カテゴリ／タグ名 → 英語 WP 側 ID のマッピング
# ==============================================================

def load_mapping() -> Dict[str, Dict[str, int]]:
    """
    戻り値:
      {
        \"categories\": {\"未来教育\": 42, ...},
        \"tags\":       {\"生成AI\":  99, ...}
      }
    """
    mapping = {"categories": {}, "tags": {}}

    if CATEGORY_MAP_FILE.exists():
        mapping["categories"] = json.loads(CATEGORY_MAP_FILE.read_text())

    if TAG_MAP_FILE.exists():
        mapping["tags"] = json.loads(TAG_MAP_FILE.read_text())

    return mapping

# ==============================================================
# WordPress Basic 認証ヘッダー生成
# ==============================================================

def basic_auth(user: str, app_pass: str) -> Dict[str, str]:
    token = base64.b64encode(f\"{user}:{app_pass}\".encode()).decode()
    return {\"Authorization\": f\"Basic {token}\"}
