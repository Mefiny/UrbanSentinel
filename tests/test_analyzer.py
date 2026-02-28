"""Tests for backend.analyzer module."""
from datetime import datetime
from backend.models import Signal, SourceType, RiskCategory, EconomicImpact
from backend.analyzer import analyze_signal, _match_category, _assess_severity


def _make_signal(text, source="news"):
    return Signal(
        id="TEST-001",
        text=text,
        source=SourceType(source),
        location="District A",
        timestamp=datetime(2026, 2, 27, 12, 0, 0),
    )


# ── Category matching tests ──────────────────────────────────

class TestMatchCategory:
    def test_crime_robbery(self):
        cat, kw = _match_category("Armed robbery reported at convenience store")
        assert cat == RiskCategory.crime
        assert "robbery" in kw

    def test_crime_violence(self):
        cat, kw = _match_category("Domestic violence calls increased this month")
        assert cat == RiskCategory.crime
        assert "violence" in kw

    def test_traffic_accident(self):
        cat, kw = _match_category("Multi-vehicle collision on expressway")
        assert cat == RiskCategory.traffic
        assert "collision" in kw

    def test_fraud_scam(self):
        cat, kw = _match_category("Phishing scam targeting residents via email")
        assert cat == RiskCategory.fraud
        assert "scam" in kw or "phishing" in kw

    def test_infrastructure_collapse(self):
        cat, kw = _match_category("Bridge collapse near downtown area")
        assert cat == RiskCategory.infrastructure
        assert "collapse" in kw

    def test_default_category(self):
        cat, kw = _match_category("Nothing special happening today")
        assert cat == RiskCategory.infrastructure  # default fallback

    def test_max_five_keywords(self):
        text = "robbery theft assault vandalism drug gang violence"
        _, kw = _match_category(text)
        assert len(kw) <= 5


# ── Severity assessment tests ────────────────────────────────

class TestAssessSeverity:
    def test_high_severity_multiple(self):
        level, impact = _assess_severity("Armed man killed two, child injured")
        assert level == 5
        assert impact == EconomicImpact.high

    def test_high_severity_single(self):
        level, impact = _assess_severity("Building collapse reported downtown")
        assert level == 4
        assert impact == EconomicImpact.high

    def test_medium_severity_multiple(self):
        level, impact = _assess_severity("Road closed and blocked after damage")
        assert level == 3
        assert impact == EconomicImpact.medium

    def test_medium_severity_single(self):
        level, impact = _assess_severity("Lane blocked on highway")
        assert level == 2
        assert impact == EconomicImpact.medium

    def test_low_severity(self):
        level, impact = _assess_severity("Minor complaint filed by resident")
        assert level == 1
        assert impact == EconomicImpact.low


# ── Integration tests for analyze_signal ─────────────────────

class TestAnalyzeSignal:
    def test_crime_signal(self):
        sig = _make_signal("Armed robbery at downtown bank. Two injured.")
        result = analyze_signal(sig)
        assert result.category == RiskCategory.crime
        assert result.risk_level >= 4
        assert result.economic_impact == EconomicImpact.high
        assert 0.0 <= result.confidence <= 1.0
        assert len(result.keywords) >= 1
        assert len(result.summary) > 0

    def test_traffic_signal(self):
        sig = _make_signal("Bus suspended after brake failure on route 42.")
        result = analyze_signal(sig)
        assert result.category == RiskCategory.traffic
        assert result.risk_level >= 2

    def test_fraud_signal(self):
        sig = _make_signal("Cryptocurrency scam targeting retirees with fake returns.")
        result = analyze_signal(sig)
        assert result.category == RiskCategory.fraud

    def test_infrastructure_signal(self):
        sig = _make_signal("Power outage affecting 12,000 households in northern district.")
        result = analyze_signal(sig)
        assert result.category == RiskCategory.infrastructure
        assert result.risk_level >= 4

    def test_confidence_range(self):
        sig = _make_signal("Robbery and theft reported near school.")
        result = analyze_signal(sig)
        assert 0.5 <= result.confidence <= 0.95

    def test_summary_contains_category(self):
        sig = _make_signal("Sinkhole opened on Highway 7.")
        result = analyze_signal(sig)
        assert result.category.value in result.summary


# ── Chinese signal analysis tests ─────────────────────────────

class TestAnalyzeChineseSignal:
    def test_zh_crime(self):
        sig = _make_signal("市中心发生持刀抢劫事件，一名受害者受伤送医。")
        result = analyze_signal(sig)
        assert result.category == RiskCategory.crime

    def test_zh_traffic(self):
        sig = _make_signal("三号线地铁因信号故障停运，数千名乘客滞留。")
        result = analyze_signal(sig)
        assert result.category == RiskCategory.traffic

    def test_zh_fraud(self):
        sig = _make_signal("多名居民举报电信诈骗，骗子冒充公安局要求转账。")
        result = analyze_signal(sig)
        assert result.category == RiskCategory.fraud

    def test_zh_infrastructure(self):
        sig = _make_signal("暴雨导致路面积水严重，部分地下车库被淹。")
        result = analyze_signal(sig)
        assert result.category == RiskCategory.infrastructure

    def test_zh_summary_format(self):
        sig = _make_signal("高速公路连环追尾事故，交通严重拥堵。")
        result = analyze_signal(sig)
        assert "风险检测" in result.summary
