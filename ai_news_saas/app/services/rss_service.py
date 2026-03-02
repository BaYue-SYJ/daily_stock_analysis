from newspaper import Article as NewsArticle
import feedparser


def crawl_rss(url: str) -> list[dict]:
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:20]:
        article = NewsArticle(entry.link)
        article.download()
        article.parse()
        items.append({"title": entry.title, "link": entry.link, "content": article.text})
    return items
