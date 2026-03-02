from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.saas_models import WechatAccount


@dataclass
class WechatPublishResult:
    media_id: str
    draft_media_id: str
    publish_id: str


class WechatPublisher:
    """WeChat Official Account publisher.

    Implements official endpoints:
    - Get access_token: /cgi-bin/token
    - Upload cover image: /cgi-bin/material/add_material?type=image
    - Add draft: /cgi-bin/draft/add
    - Publish draft: /cgi-bin/freepublish/submit
    """

    def __init__(self, db: Session | None = None):
        self.db = db or SessionLocal()
        self._owns_db = db is None

    def close(self) -> None:
        if self._owns_db:
            self.db.close()

    def _wechat_get(self, path: str, params: dict) -> dict:
        url = f"{settings.WECHAT_API_BASE_URL}{path}"
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if data.get("errcode", 0) != 0:
            raise RuntimeError(f"WeChat API error: {data}")
        return data

    def _wechat_post(self, path: str, params: dict, payload: dict) -> dict:
        url = f"{settings.WECHAT_API_BASE_URL}{path}"
        resp = requests.post(url, params=params, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if data.get("errcode", 0) != 0:
            raise RuntimeError(f"WeChat API error: {data}")
        return data

    def _wechat_upload_file(self, path: str, params: dict, file_path: str) -> dict:
        url = f"{settings.WECHAT_API_BASE_URL}{path}"
        file_name = Path(file_path).name
        with open(file_path, "rb") as f:
            files = {"media": (file_name, f, "image/jpeg")}
            resp = requests.post(url, params=params, files=files, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("errcode", 0) != 0:
            raise RuntimeError(f"WeChat API error: {data}")
        return data

    def _get_account(self, tenant_id: int, wechat_account_id: int) -> WechatAccount:
        account = (
            self.db.query(WechatAccount)
            .filter(WechatAccount.tenant_id == tenant_id, WechatAccount.id == wechat_account_id)
            .first()
        )
        if not account:
            raise ValueError("WeChat account not found")
        return account

    def get_access_token(self, tenant_id: int, wechat_account_id: int, force_refresh: bool = False) -> str:
        """Auto fetch access_token with multi-account support.

        Reads account-specific app_id/app_secret and refreshes token as needed.
        """
        account = self._get_account(tenant_id, wechat_account_id)

        if (
            not force_refresh
            and account.access_token
            and account.token_expires_at
            and account.token_expires_at > datetime.utcnow() + timedelta(minutes=2)
        ):
            return account.access_token

        data = self._wechat_get(
            "/cgi-bin/token",
            params={
                "grant_type": "client_credential",
                "appid": account.app_id,
                "secret": account.app_secret,
            },
        )
        token = data["access_token"]
        expires_in = int(data.get("expires_in", 7200))

        account.access_token = token
        account.token_expires_at = datetime.utcnow() + timedelta(seconds=max(60, expires_in - 120))
        self.db.add(account)
        self.db.commit()
        return token

    def upload_cover_image(self, tenant_id: int, wechat_account_id: int, image_path: str) -> str:
        """Upload cover image and return media_id."""
        token = self.get_access_token(tenant_id, wechat_account_id)
        data = self._wechat_upload_file(
            "/cgi-bin/material/add_material",
            params={"access_token": token, "type": "image"},
            file_path=image_path,
        )
        return data["media_id"]

    def add_draft(
        self,
        tenant_id: int,
        wechat_account_id: int,
        title: str,
        author: str,
        content_html: str,
        digest: str,
        thumb_media_id: str,
        content_source_url: str,
    ) -> str:
        """Call WeChat AddDraft API and return draft media_id."""
        token = self.get_access_token(tenant_id, wechat_account_id)
        payload = {
            "articles": [
                {
                    "title": title,
                    "author": author,
                    "digest": digest,
                    "content": content_html,
                    "content_source_url": content_source_url,
                    "thumb_media_id": thumb_media_id,
                    "need_open_comment": 1,
                    "only_fans_can_comment": 0,
                }
            ]
        }
        data = self._wechat_post(
            "/cgi-bin/draft/add",
            params={"access_token": token},
            payload=payload,
        )
        return data["media_id"]

    def publish_draft(self, tenant_id: int, wechat_account_id: int, draft_media_id: str) -> str:
        """Call WeChat Publish API (freepublish/submit) and return publish_id."""
        token = self.get_access_token(tenant_id, wechat_account_id)
        data = self._wechat_post(
            "/cgi-bin/freepublish/submit",
            params={"access_token": token},
            payload={"media_id": draft_media_id},
        )
        return str(data["publish_id"])

    def publish_article_workflow(
        self,
        tenant_id: int,
        wechat_account_id: int,
        title: str,
        author: str,
        content_html: str,
        digest: str,
        content_source_url: str,
        cover_image_path: str,
    ) -> WechatPublishResult:
        """One-shot workflow: upload image -> add draft -> publish."""
        media_id = self.upload_cover_image(
            tenant_id=tenant_id,
            wechat_account_id=wechat_account_id,
            image_path=cover_image_path,
        )
        draft_media_id = self.add_draft(
            tenant_id=tenant_id,
            wechat_account_id=wechat_account_id,
            title=title,
            author=author,
            content_html=content_html,
            digest=digest,
            thumb_media_id=media_id,
            content_source_url=content_source_url,
        )
        publish_id = self.publish_draft(
            tenant_id=tenant_id,
            wechat_account_id=wechat_account_id,
            draft_media_id=draft_media_id,
        )
        return WechatPublishResult(media_id=media_id, draft_media_id=draft_media_id, publish_id=publish_id)


# 示例代码（基于微信官方接口 AddDraft + Publish）
if __name__ == "__main__":
    publisher = WechatPublisher()
    try:
        result = publisher.publish_article_workflow(
            tenant_id=1,
            wechat_account_id=1,
            title="AI 行业周报：多模态与 Agent 新进展",
            author="AI News Bot",
            content_html="<h2>本周要点</h2><p>这里放置你的总结正文 HTML。</p>",
            digest="一文速览本周 AI 前沿动态与趋势。",
            content_source_url="https://example.com/ai-news-weekly",
            cover_image_path="./cover.jpg",
        )
        print(
            {
                "thumb_media_id": result.media_id,
                "draft_media_id": result.draft_media_id,
                "publish_id": result.publish_id,
            }
        )
    finally:
        publisher.close()
