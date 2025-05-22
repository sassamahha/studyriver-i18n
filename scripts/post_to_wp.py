#!/usr/bin/env python3
"""英語 WP へ記事を投稿するユーティリティ"""
import os, requests, sys, json
from utils import basic_auth, logger

WP_URL  = os.getenv("WP_URL")  or os.getenv("WP_URL_EN")
WP_USER = os.getenv("WP_USER") or os.getenv("WP_USER_EN")
WP_PASS = os.getenv("WP_PASS") or os.getenv("WP_PASS_EN")

POST_ENDPOINT = f"{WP_URL}/wp-json/wp/v2/posts"


def create_post(payload: dict) -> int:
    headers = basic_auth(WP_USER, WP_PASS)
    headers["Content-Type"] = "application/json"
    resp = requests.post(POST_ENDPOINT, headers=headers, data=json.dumps(payload), timeout=30)
    resp.raise_for_status()
    post_id = resp.json().get("id")
    logger.info(f"Published post id={post_id}")
    return post_id

if __name__ == "__main__":
    sample_json = json.loads(sys.stdin.read())
    print(create_post(sample_json))
