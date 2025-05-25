#!/usr/bin/env python3
"""画像を WP メディアにアップロードして ID を返す"""

import base64, os, pathlib, requests
from typing import Optional

WP_URL  = os.environ["WP_URL"].rstrip("/")
AUTH    = base64.b64encode(
            f'{os.environ["WP_USER"]}:{os.environ["WP_PASS"]}'.encode()
          ).decode()
HEADERS = {"Authorization": f"Basic {AUTH}"}

TMP_DIR = pathlib.Path("/tmp")
TMP_DIR.mkdir(exist_ok=True)

def upload_image(src_url: str) -> Optional[int]:
    """src_url をダウンロードして WP に upload。失敗時 None"""
    try:
        fname = src_url.split("/")[-1]
        tmp   = TMP_DIR / fname
        tmp.write_bytes(requests.get(src_url, timeout=10).content)

        files = {"file": (fname, tmp.open("rb"), "application/octet-stream")}
        r = requests.post(
            f"{WP_URL}/media",
            headers=HEADERS | {"Content-Disposition": f'attachment; filename=\"{fname}\"'},
            files=files,
            timeout=15
        )
        r.raise_for_status()
        return r.json().get("id")
    except Exception as e:
        print(f"[upload_media] {e}")
        return None
