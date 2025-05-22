#!/usr/bin/env python3
"""画像をダウンロードし、対象 WP に再アップロード"""

import os, requests, mimetypes, tempfile, pathlib, sys
from utils import basic_auth, logger

# 汎用 → EN fallback
WP_URL  = os.getenv("WP_URL")  or os.getenv("WP_URL_EN")
WP_USER = os.getenv("WP_USER") or os.getenv("WP_USER_EN")
WP_PASS = os.getenv("WP_PASS") or os.getenv("WP_PASS_EN")

if not WP_URL:
    logger.error("WP_URL not set"); sys.exit(1)

MEDIA_ENDPOINT = f"{WP_URL}/wp-json/wp/v2/media"   # ← ここを修正

def upload_image(img_url: str) -> int:
    resp = requests.get(img_url, timeout=15)
    resp.raise_for_status()

    ext  = pathlib.Path(img_url).suffix or ".jpg"
    mime = mimetypes.types_map.get(ext, "image/jpeg")

    with tempfile.NamedTemporaryFile(suffix=ext) as tmp:
        tmp.write(resp.content)
        tmp.flush()

        headers = basic_auth(WP_USER, WP_PASS)
        headers.update({
            "Content-Disposition": f"attachment; filename=upload{ext}",
            "Content-Type": mime,
        })
        files = {"file": (tmp.name, open(tmp.name, "rb"), mime)}
        up = requests.post(MEDIA_ENDPOINT, headers=headers, files=files, timeout=30)
        up.raise_for_status()
        media_id = up.json().get("id")
        logger.info(f"Uploaded image → media_id={media_id}")
        return media_id
