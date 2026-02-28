"""Tests for backend.language module."""
from backend.language import detect_language, match_zh_category
from backend.models import RiskCategory


class TestDetectLanguage:
    def test_english_text(self):
        assert detect_language("Armed robbery at downtown bank") == "en"

    def test_chinese_text(self):
        assert detect_language("市中心发生持刀抢劫事件") == "zh"

    def test_mixed_mostly_english(self):
        assert detect_language("The bridge on 5th Avenue collapsed") == "en"

    def test_mixed_mostly_chinese(self):
        assert detect_language("三号线地铁因信号故障停运") == "zh"

    def test_empty_string(self):
        assert detect_language("") == "en"


class TestMatchZhCategory:
    def test_crime_keywords(self):
        cat, kw = match_zh_category("市中心发生持刀抢劫事件，受害者受伤")
        assert cat == RiskCategory.crime
        assert "抢劫" in kw

    def test_traffic_keywords(self):
        cat, kw = match_zh_category("地铁因信号故障停运，交通拥堵严重")
        assert cat == RiskCategory.traffic
        assert any(k in kw for k in ["地铁", "故障", "停运", "交通", "拥堵"])

    def test_fraud_keywords(self):
        cat, kw = match_zh_category("多名居民举报电信诈骗，骗子冒充公安局")
        assert cat == RiskCategory.fraud
        assert "诈骗" in kw

    def test_infrastructure_keywords(self):
        cat, kw = match_zh_category("暴雨导致路面积水严重，地下车库被淹")
        assert cat == RiskCategory.infrastructure
        assert "积水" in kw

    def test_returns_keywords_list(self):
        _, kw = match_zh_category("抢劫盗窃暴力犯罪帮派斗殴")
        assert len(kw) <= 5
