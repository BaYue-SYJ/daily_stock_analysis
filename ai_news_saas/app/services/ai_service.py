from openai import OpenAI

from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def summarize_article(content: str) -> str:
    prompt = "请将以下 AI 行业文章总结成公众号风格的中文精华（150 字左右）：\n\n" + content
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    return response.choices[0].message.content or ""
