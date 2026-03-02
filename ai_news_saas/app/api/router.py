from fastapi import APIRouter

from app.api import accounts, api, auth, content, publish, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(accounts.router)
api_router.include_router(content.router)
api_router.include_router(publish.router)
api_router.include_router(api.router)
