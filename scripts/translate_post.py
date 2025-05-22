#!/usr/bin/env python3
"""Queue → GPT 翻訳 → 画像 UP → WP 投稿（JSON 崩れ自動修正）"""
import os, json, pathlib, requests, re, argparse, sys
from slugify import slugify
from openai import OpenAI
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]/"scripts"))
from utils import logger, load_mapping
from upload_media import upload_image
from post_to_wp import create_post

# -------- Args & env --------
parser = argparse.ArgumentParser()
parser.add_argument("--lang", default=os.getenv("TARGET_LANG", "en"))
args = parser.parse_args()
LANG = args.lang.lower()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
QUEUE_FILE = pathlib.Path("data/rss_queue.json")
if not QUEUE_FILE.exists():
    logger.info("Queue empty"); sys.exit(0)

mapping = load_mapping()
cat_map = mapping.get("categories", {})
tag_map = mapping.get("tags", {})

queue = json.loads(QUEUE_FILE.read_text())

json_re = re.compile(r"\{[\s\S]+\}")

def safe_json(text: str):
    """GPT 出力から最初の {...} を抜き出して JSON.loads"""
    m = json_re.search(text)
    if not m:
        raise ValueError("JSON block not found")
    return json.loads(m.group(0))

for item in queue:
    logger.info(f"Translating post_id={item['post_id']}")
    # 1) 元記事
    jp = requests.get(f"https://studyriver.jp/wp-json/wp/v2/posts/{item['post_id']}?_embed").json()
    jp_content = jp['content']['rendered']

    # 2) GPT 翻訳
    prompt = {
        "role": "user",
        "content": f"""
Return ONLY valid JSON like {{\"title\":...,\"content\":...,\"excerpt\":...}} translating the article below to {LANG}.
Keep HTML tags and lists, no markdown fences.
---\n{jp_content}
"""
    }
    rsp = client.chat.completions.create(model="gpt-4o-mini", messages=[prompt])
    try:
        tr = safe_json(rsp.choices[0].message.content)
    except Exception as e:
        logger.error(f"JSON parse error: {e}\nRAW>> {rsp.choices[0].message.content[:200]}")
        continue  # skip this item

    # 3) アイキャッチ再アップ
    media_id_en = None
    fid = jp.get('featured_media')
    if fid:
        src = requests.get(f"https://studyriver.jp/wp-json/wp/v2/media/{fid}").json()['source_url']
        media_id_en = upload_image(src)

    # 4) taxonomy map
    cats = [cat_map.get(n) for n in [c['name'] for c in jp.get('_embedded', {}).get('wp:term', [[]])[0]] if cat_map.get(n)]
    tags = [tag_map.get(n) for n in [t['name'] for t in jp.get('_embedded', {}).get('wp:term', [[],[]])[1]] if tag_map.get(n)]

    # 5) 投稿
    payload = {
        "title": tr["title"],
        "content": tr["content"],
        "excerpt": tr["excerpt"],
        "slug": f"{LANG}-{slugify(tr['title'])}" if LANG!="en" else slugify(tr['title']),
        "featured_media": media_id_en,
        "categories": cats,
        "tags": tags,
        "status": "publish"
    }
    try:
        create_post(payload)
    except Exception as e:
        logger.error(f"WP post error: {e}")
        continue

logger.info("Finished processing queue")
QUEUE_FILE.unlink()
