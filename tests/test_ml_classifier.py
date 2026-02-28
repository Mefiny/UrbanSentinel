"""Tests for backend.ml_classifier module."""
from backend.ml_classifier import get_classifier, RiskClassifier, _preprocess
from backend.models import RiskCategory


class TestPreprocess:
    def test_lowercase(self):
        assert _preprocess("Armed ROBBERY") == "armed robbery"

    def test_strip_punctuation(self):
        assert _preprocess("hello, world!") == "hello world"

    def test_collapse_whitespace(self):
        assert _preprocess("too   many   spaces") == "too many spaces"


class TestRiskClassifier:
    def test_singleton(self):
        c1 = get_classifier()
        c2 = get_classifier()
        assert c1 is c2

    def test_predict_crime(self):
        clf = get_classifier()
        cat, conf = clf.predict("Armed robbery at downtown bank")
        assert cat == RiskCategory.crime
        assert 0.0 < conf <= 1.0

    def test_predict_traffic(self):
        clf = get_classifier()
        cat, _ = clf.predict("Multi-vehicle collision on highway")
        assert cat == RiskCategory.traffic

    def test_predict_fraud(self):
        clf = get_classifier()
        cat, _ = clf.predict("Phishing scam targeting elderly residents")
        assert cat == RiskCategory.fraud

    def test_predict_infrastructure(self):
        clf = get_classifier()
        cat, _ = clf.predict("Power outage affecting thousands of homes")
        assert cat == RiskCategory.infrastructure

    def test_predict_top_n(self):
        clf = get_classifier()
        results = clf.predict_top_n("Robbery near bridge collapse zone", n=2)
        assert len(results) == 2
        assert all(0.0 < p <= 1.0 for _, p in results)

    def test_confidence_sums_to_one(self):
        clf = get_classifier()
        results = clf.predict_top_n("Random urban event", n=4)
        total = sum(p for _, p in results)
        assert 0.99 <= total <= 1.01
