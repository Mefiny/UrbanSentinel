"""
Real-time news fetcher using GNews API.

Fetches urban safety related news articles and converts them
into Signal objects for AI risk analysis.
"""
import httpx
from datetime import datetime
from typing import List, Optional
from backend.models import Signal, SourceType
from config import GNEWS_API_KEY, GNEWS_BASE_URL


# Search queries for urban risk topics
RISK_QUERIES = [
    "urban crime robbery assault",
    "traffic accident collision",
    "fraud scam phishing",
    "infrastructure collapse flood power outage",
]


def fetch_news(query: str, lang: str = "en", country: Optional[str] = None, max_results: int = 5) -> List[dict]:
    """Fetch news articles from GNews API."""
    url = f"{GNEWS_BASE_URL}/search"
    params = {
        "q": query,
        "lang": lang,
        "max": max_results,
        "token": GNEWS_API_KEY,
    }
    if country:
        params["country"] = country
    try:
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("articles", [])
    except Exception:
        return []


def article_to_signal(article: dict, idx: int) -> Optional[Signal]:
    """Convert a GNews article to a Signal object."""
    title = article.get("title", "")
    desc = article.get("description", "")
    text = f"{title}. {desc}" if desc else title
    if not text.strip():
        return None

    published = article.get("publishedAt", "")
    try:
        ts = datetime.fromisoformat(published.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        ts = datetime.now()

    source_name = article.get("source", {}).get("name", "")
    return Signal(
        id=f"NEWS-{idx:03d}",
        text=text,
        source=SourceType.news,
        location=source_name or "Unknown",
        timestamp=ts,
    )


def fetch_risk_news(lang: str = "en", country: Optional[str] = None, per_query: int = 3) -> List[Signal]:
    """Fetch news for all risk categories and return as Signal list."""
    signals = []
    idx = 1
    for query in RISK_QUERIES:
        articles = fetch_news(query, lang=lang, country=country, max_results=per_query)
        for article in articles:
            sig = article_to_signal(article, idx)
            if sig:
                signals.append(sig)
                idx += 1
    return signals
