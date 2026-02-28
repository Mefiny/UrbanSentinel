"""Tests for backend.news_fetcher module."""
from datetime import datetime
from unittest.mock import patch, MagicMock
from backend.news_fetcher import fetch_news, article_to_signal, fetch_risk_news
from backend.models import SourceType


SAMPLE_ARTICLE = {
    "title": "Armed robbery reported downtown",
    "description": "Police respond to armed robbery at local bank.",
    "publishedAt": "2026-02-28T10:00:00Z",
    "source": {"name": "City News"},
}


class TestArticleToSignal:
    def test_basic_conversion(self):
        sig = article_to_signal(SAMPLE_ARTICLE, 1)
        assert sig is not None
        assert sig.id == "NEWS-001"
        assert sig.source == SourceType.news
        assert "Armed robbery" in sig.text
        assert sig.location == "City News"

    def test_missing_description(self):
        article = {"title": "Breaking news", "publishedAt": "2026-02-28T10:00:00Z", "source": {"name": "AP"}}
        sig = article_to_signal(article, 5)
        assert sig is not None
        assert sig.text == "Breaking news"
        assert sig.id == "NEWS-005"

    def test_empty_text_returns_none(self):
        article = {"title": "", "description": "", "publishedAt": "", "source": {}}
        sig = article_to_signal(article, 1)
        assert sig is None

    def test_invalid_date_fallback(self):
        article = {"title": "Test", "publishedAt": "not-a-date", "source": {"name": "X"}}
        sig = article_to_signal(article, 1)
        assert sig is not None
        assert isinstance(sig.timestamp, datetime)

    def test_missing_source_name(self):
        article = {"title": "Test", "publishedAt": "2026-02-28T10:00:00Z", "source": {}}
        sig = article_to_signal(article, 2)
        assert sig.location == "Unknown"

    def test_index_formatting(self):
        sig = article_to_signal(SAMPLE_ARTICLE, 42)
        assert sig.id == "NEWS-042"


class TestFetchNews:
    @patch("backend.news_fetcher.httpx.get")
    def test_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"articles": [SAMPLE_ARTICLE]}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        result = fetch_news("crime")
        assert len(result) == 1
        assert result[0]["title"] == "Armed robbery reported downtown"

    @patch("backend.news_fetcher.httpx.get")
    def test_empty_response(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"articles": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp
        result = fetch_news("nothing")
        assert result == []

    @patch("backend.news_fetcher.httpx.get")
    def test_network_error(self, mock_get):
        mock_get.side_effect = Exception("Connection failed")
        result = fetch_news("crime")
        assert result == []


class TestFetchRiskNews:
    @patch("backend.news_fetcher.fetch_news")
    def test_aggregates_all_queries(self, mock_fn):
        mock_fn.return_value = [SAMPLE_ARTICLE]
        signals = fetch_risk_news(per_query=1)
        assert len(signals) == 4  # one article per query, 4 queries
        assert all(s.source == SourceType.news for s in signals)

    @patch("backend.news_fetcher.fetch_news")
    def test_empty_results(self, mock_fn):
        mock_fn.return_value = []
        signals = fetch_risk_news()
        assert signals == []
