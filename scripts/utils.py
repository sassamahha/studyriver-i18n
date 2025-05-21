import json, logging, os, base64, pathlib, hashlib
from typing import Dict, List

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(format="[%(levelname)s] %(message)s", level=LOG_LEVEL)
logger = logging.getLogger(__name__)

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

PROCESSED_FILE = DATA_DIR / "processed.json"
MAPPING_FILE   = DATA_DIR / "category_mapping.json"

# ------------------------------
# キャッシュ読み書き
# ------------------------------

def load_mapping() -> Dict[str, Dict[str, int]]:
    category_file = ROOT / "config" / "category_mapping.json"
    tag_file = ROOT / "config" / "tag_mapping.json"

    mapping = {
        "categories": {},
        "tags": {}
    }

    if category_file.exists():
        with category_file.open() as f:
            mapping["categories"] = json.load(f)

    if tag_file.exists():
        with tag_file.open() as f:
            mapping["tags"] = json.load(f)

    return mapping

def save_processed(ids: List[int]):
    PROCESSED_FILE.write_text(json.dumps({"processed": ids}, ensure_ascii=False, indent=2))

# ------------------------------
# カテゴリ名→ID 変換
# ------------------------------

def load_mapping() -> Dict[str, int]:
    if not MAPPING_FILE.exists():
        return {}
    return json.loads(MAPPING_FILE.read_text())

# ------------------------------
# Basic 認証ヘッダー生成
# ------------------------------

def basic_auth(user: str, app_pass: str) -> Dict[str, str]:
    auth = base64.b64encode(f"{user}:{app_pass}".encode()).decode()
    return {"Authorization": f"Basic {auth}"}
