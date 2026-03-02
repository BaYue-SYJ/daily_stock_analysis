from __future__ import annotations

import json
import re
from dataclasses import dataclass

from openai import OpenAI

from app.core.config import settings


@dataclass
class SummaryResult:
    summarized_body: str
    suggested_titles: list[str]
    abstract: str
    raw_output: str


DEFAULT_SUMMARIZER_PROMPT = (
    "你是一名专业科技编辑。请基于给定文章标题和链接，输出结构化 JSON，总结为中文内容。\n"
    "必须严格返回 JSON，格式如下：\n"
    "{\n"
    '  "summarized_body": "...",\n'
    '  "suggested_titles": ["标题1", "标题2", "标题3", "标题4", "标题5"],\n'
    '  "abstract": "..."\n'
    "}\n"
    "要求：\n"
    "1) summarized_body: 300~600 字；\n"
    "2) suggested_titles: 必须恰好 5 个；\n"
    "3) abstract: 80~150 字；\n"
    "4) 内容面向 AI 行业读者，风格清晰专业。"
)


class ArticleSummarizer:
    def __init__(
        self,
        model: str | None = None,
        prompt_template: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model or settings.OPENAI_MODEL
        self.prompt_template = prompt_template or getattr(settings, "SUMMARIZER_PROMPT", DEFAULT_SUMMARIZER_PROMPT)
        self.client = OpenAI(api_key=api_key or settings.OPENAI_API_KEY)

    @staticmethod
    def _extract_json(raw_text: str) -> dict:
        cleaned = raw_text.strip()
        fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, flags=re.S)
        if fenced:
            cleaned = fenced.group(1)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(cleaned[start : end + 1])
            raise

    @staticmethod
    def _normalize_titles(titles: list[str] | None) -> list[str]:
        titles = [t.strip() for t in (titles or []) if isinstance(t, str) and t.strip()]
        if len(titles) >= 5:
            return titles[:5]
        while len(titles) < 5:
            titles.append(f"AI 前沿速览 #{len(titles) + 1}")
        return titles

    def summarize(self, article_title: str, article_link: str) -> SummaryResult:
        user_prompt = (
            f"文章标题：{article_title}\n"
            f"文章链接：{article_link}\n\n"
            "请按系统要求生成 JSON。"
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.prompt_template},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )
        raw_output = response.choices[0].message.content or ""
        data = self._extract_json(raw_output)

        summarized_body = str(data.get("summarized_body", "")).strip()
        abstract = str(data.get("abstract", "")).strip()
        suggested_titles = self._normalize_titles(data.get("suggested_titles"))

        return SummaryResult(
            summarized_body=summarized_body,
            suggested_titles=suggested_titles,
            abstract=abstract,
            raw_output=raw_output,
        )
