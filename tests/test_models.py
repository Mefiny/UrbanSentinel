"""Tests for backend.models module."""
import pytest
from datetime import datetime
from pydantic import ValidationError
from backend.models import (
    Signal, RiskAnalysis, PrioritizedAlert,
    SourceType, RiskCategory, EconomicImpact,
)


class TestSignal:
    def test_valid_signal(self):
        s = Signal(
            id="SIG-001", text="Test", source=SourceType.news,
            location="District A", timestamp=datetime(2026, 2, 27),
        )
        assert s.id == "SIG-001"
        assert s.source == SourceType.news

    def test_all_source_types(self):
        for src in SourceType:
            s = Signal(
                id="T", text="T", source=src,
                location="X", timestamp=datetime.now(),
            )
            assert s.source == src


class TestRiskAnalysis:
    def test_valid_analysis(self):
        a = RiskAnalysis(
            category=RiskCategory.crime, risk_level=3,
            economic_impact=EconomicImpact.medium,
            confidence=0.8, keywords=["theft"], summary="Test.",
        )
        assert a.risk_level == 3

    def test_risk_level_too_high(self):
        with pytest.raises(ValidationError):
            RiskAnalysis(
                category=RiskCategory.crime, risk_level=6,
                economic_impact=EconomicImpact.low,
                confidence=0.5, keywords=[], summary="X",
            )

    def test_risk_level_too_low(self):
        with pytest.raises(ValidationError):
            RiskAnalysis(
                category=RiskCategory.crime, risk_level=0,
                economic_impact=EconomicImpact.low,
                confidence=0.5, keywords=[], summary="X",
            )

    def test_confidence_out_of_range(self):
        with pytest.raises(ValidationError):
            RiskAnalysis(
                category=RiskCategory.crime, risk_level=3,
                economic_impact=EconomicImpact.low,
                confidence=1.5, keywords=[], summary="X",
            )
