"""Tests for backend.scorer module."""
from datetime import datetime, timezone, timedelta
from backend.models import (
    Signal, RiskAnalysis, SourceType, RiskCategory, EconomicImpact,
)
from backend.scorer import compute_priority, prioritize_alerts, _recency_weight


def _make_signal(source="government", hours_ago=0):
    ts = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return Signal(
        id="TEST-001", text="Test signal",
        source=SourceType(source), location="District A", timestamp=ts,
    )


def _make_analysis(risk=3, impact=EconomicImpact.medium):
    return RiskAnalysis(
        category=RiskCategory.crime, risk_level=risk,
        economic_impact=impact, confidence=0.8,
        keywords=["test"], summary="Test summary.",
    )


# ── Recency weight tests ─────────────────────────────────────

class TestRecencyWeight:
    def test_within_one_hour(self):
        assert _recency_weight(datetime.now(timezone.utc)) == 1.0

    def test_within_six_hours(self):
        ts = datetime.now(timezone.utc) - timedelta(hours=3)
        assert _recency_weight(ts) == 0.8

    def test_within_24_hours(self):
        ts = datetime.now(timezone.utc) - timedelta(hours=12)
        assert _recency_weight(ts) == 0.5

    def test_within_72_hours(self):
        ts = datetime.now(timezone.utc) - timedelta(hours=48)
        assert _recency_weight(ts) == 0.3

    def test_older_than_72_hours(self):
        ts = datetime.now(timezone.utc) - timedelta(hours=100)
        assert _recency_weight(ts) == 0.1


# ── Priority computation tests ───────────────────────────────

class TestComputePriority:
    def test_score_range(self):
        sig = _make_signal()
        ana = _make_analysis(risk=5, impact=EconomicImpact.high)
        score = compute_priority(sig, ana)
        assert 0.0 <= score <= 1.0

    def test_high_risk_scores_higher(self):
        sig = _make_signal()
        high = compute_priority(sig, _make_analysis(risk=5, impact=EconomicImpact.high))
        low = compute_priority(sig, _make_analysis(risk=1, impact=EconomicImpact.low))
        assert high > low

    def test_government_source_scores_higher(self):
        ana = _make_analysis()
        gov = compute_priority(_make_signal(source="government"), ana)
        social = compute_priority(_make_signal(source="social_media"), ana)
        assert gov > social

    def test_recent_signal_scores_higher(self):
        ana = _make_analysis()
        recent = compute_priority(_make_signal(hours_ago=0), ana)
        old = compute_priority(_make_signal(hours_ago=100), ana)
        assert recent > old


# ── Ranking tests ────────────────────────────────────────────

class TestPrioritizeAlerts:
    def test_ranking_order(self):
        sig1 = _make_signal()
        sig2 = _make_signal()
        ana_high = _make_analysis(risk=5, impact=EconomicImpact.high)
        ana_low = _make_analysis(risk=1, impact=EconomicImpact.low)
        alerts = prioritize_alerts([(sig1, ana_low), (sig2, ana_high)])
        assert alerts[0].rank == 1
        assert alerts[0].analysis.risk_level == 5
        assert alerts[1].rank == 2

    def test_empty_input(self):
        assert prioritize_alerts([]) == []

    def test_single_alert(self):
        alerts = prioritize_alerts([(_make_signal(), _make_analysis())])
        assert len(alerts) == 1
        assert alerts[0].rank == 1
