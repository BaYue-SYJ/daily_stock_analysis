from datetime import datetime

from pydantic import BaseModel, HttpUrl


class RssSourceCreate(BaseModel):
    name: str
    url: HttpUrl


class ArticleResponse(BaseModel):
    id: int
    title: str
    link: str
    summary: str
    published_at: datetime | None
