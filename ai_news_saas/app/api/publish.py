from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_tenant_id
from app.models.entities import Article, PublishLog, WechatAccount
from app.services.wechat_service import publish_to_wechat

router = APIRouter(prefix="/publish", tags=["publish"])


@router.post("/wechat")
def publish_article_to_wechat(
    article_id: int,
    wechat_account_id: int,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(db_session),
):
    article = db.query(Article).filter(Article.id == article_id, Article.tenant_id == tenant_id).first()
    account = (
        db.query(WechatAccount)
        .filter(WechatAccount.id == wechat_account_id, WechatAccount.tenant_id == tenant_id)
        .first()
    )
    if not article or not account:
        raise HTTPException(status_code=404, detail="article or account not found")

    result = publish_to_wechat(access_token="replace-with-real-token", title=article.title, content=article.summary)
    log = PublishLog(
        tenant_id=tenant_id,
        article_id=article.id,
        wechat_account_id=account.id,
        status="success" if result.get("errcode", 0) == 0 else "failed",
        response_payload=str(result),
    )
    db.add(log)
    db.commit()
    return result
