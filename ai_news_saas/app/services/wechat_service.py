import requests

from app.core.config import settings


def publish_to_wechat(access_token: str, title: str, content: str) -> dict:
    url = f"{settings.WECHAT_API_BASE_URL}/cgi-bin/draft/add?access_token={access_token}"
    payload = {
        "articles": [
            {
                "title": title,
                "author": "AI Bot",
                "content": content,
                "thumb_media_id": "",
                "digest": content[:120],
            }
        ]
    }
    resp = requests.post(url, json=payload, timeout=20)
    return resp.json()
