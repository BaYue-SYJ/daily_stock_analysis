from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import db_session, get_current_tenant_id
from app.models.entities import WechatAccount

router = APIRouter(prefix="/accounts", tags=["accounts"])


class WechatAccountCreate(BaseModel):
    account_name: str
    app_id: str
    app_secret: str


@router.post("/wechat")
def bind_wechat_account(
    payload: WechatAccountCreate,
    tenant_id: int = Depends(get_current_tenant_id),
    db: Session = Depends(db_session),
):
    account = WechatAccount(tenant_id=tenant_id, **payload.model_dump())
    db.add(account)
    db.commit()
    return {"id": account.id, "message": "wechat account bound"}
