#!/usr/bin/env python3
"""RSS キューを読み取り→ GPT-4o 翻訳 → 画像 UP → Post"""
import os, json, pathlib, requests, re
from slugify import slugify
from openai import OpenAI
from utils import logger, load_mapping
from upload_media import upload_image
from post_to_wp import create_post

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

QUEUE_FILE = pathlib.Path("data/rss_queue.json")
if not QUEUE_FILE.exists():
    logger.info("Queue empty"); exit()

mapping = load_mapping()
queue = json.loads(QUEUE_FILE.read_text())

for item in queue:
    logger.info(f"Translating post_id={item['post_id']}")

    # 1) 日本語 WP から REST API で元記事詳細取得（HTML 含む）
    res = requests.get(f"https://studyriver.jp/wp-json/wp/v2/posts/{item['post_id']}")
    res.raise_for_status()
    jp_post = res.json()

    jp_title = jp_post['title']['rendered']
    jp_content = jp_post['content']['rendered']
    cat_names = [c['name'] for c in jp_post.get('_embedded', {{}}).get('wp:term', [[]])[0]] if '_embedded' in jp_post else []

    # 2) GPT 翻訳
    prompt = {
        "role": "user",
        "content": f"""
        Translate the following Japanese WordPress article to English. Keep html tags as-is. Keep lists / headings.
        Return JSON: {{\n  \"title\": <string>,\n  \"content\": <string>,\n  \"excerpt\": <string>\n}}.
        ---
        {jp_content}
        """
    }
    rsp = client.chat.completions.create(model="gpt-4o-mini", messages=[prompt])
    tr = json.loads(rsp.choices[0].message.content)

    # 3) 画像処理 (featured_media のみ)
    feat_media_id = jp_post.get('featured_media')
    media_id_en = None
    if feat_media_id:
        media_detail = requests.get(f"https://studyriver.jp/wp-json/wp/v2/media/{feat_media_id}").json()
        img_url = media_detail['source_url']
        media_id_en = upload_image(img_url)

    # 4) カテゴリ map
    cat_ids_en = [mapping.get(name) for name in cat_names if name in mapping]

    # 5) カテゴリ map
    tag_ids_en = [mapping["tags"].get(name) for name in tag_names if name in mapping["tags"]]

    # 6) 投稿
    payload = {
        "title": tr["title"],
        "content": tr["content"],
        "excerpt": tr["excerpt"],
        "slug": slugify(tr["title"]),
        "featured_media": media_id_en,
        "categories": [i for i in cat_ids_en if i],
        "tags": [i for i in tag_ids_en if i],
        "status": "publish"
    }
    create_post(payload)

logger.info("Finished processing queue")
QUEUE_FILE.unlink()