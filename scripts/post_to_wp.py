import os, json, base64, requests, pathlib
from utils import slugify_for_lang

WP_URL  = os.environ["WP_URL"].rstrip("/")
AUTH    = base64.b64encode(f"{os.environ['WP_USER']}:{os.environ['WP_PASS']}").decode()
HEADERS = {
    "Authorization": f"Basic {AUTH}",
    "Content-Type": "application/json"
}

LANGS = [
    "en", "es", "zhhans", "zhhant", "pt", "id", "fr", "it", "de"
]

RAW_DIR = pathlib.Path("data/translated")

def post_article(path: pathlib.Path):
    ja_id = json.loads(path.read_text())['ja_id']
    for lang in LANGS:
        payload = json.load((RAW_DIR / f"{lang}_{path.stem}.json").open())
        payload["slug"] = slugify_for_lang(payload["title"], lang)
        payload["status"] = "publish"
        payload["translations"] = {"ja": ja_id}
        url = f"{WP_URL}/posts?lang={lang}"
        r = requests.post(url, headers=HEADERS, data=json.dumps(payload))
        r.raise_for_status()
        print(f"✓ {lang} ->", r.json().get("link"))

if __name__ == "__main__":
    for file in RAW_DIR.glob("*.json"):
        post_article(file)
