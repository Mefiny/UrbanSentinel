from __future__ import annotations
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    government = "government"
    news = "news"
    citizen_report = "citizen_report"
    social_media = "social_media"


class RiskCategory(str, Enum):
    crime = "Crime"
    traffic = "Traffic"
    fraud = "Fraud"
    infrastructure = "Infrastructure Failure"


class EconomicImpact(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


class Signal(BaseModel):
    """Raw public signal input."""
    id: str
    text: str
    source: SourceType
    location: str
    timestamp: datetime


class RiskAnalysis(BaseModel):
    """Structured output from LLM risk analysis."""
    category: RiskCategory
    risk_level: int = Field(ge=1, le=5)
    economic_impact: EconomicImpact
    confidence: float = Field(ge=0.0, le=1.0)
    keywords: list[str]
    summary: str


class PrioritizedAlert(BaseModel):
    """Final scored alert ready for dashboard."""
    signal: Signal
    analysis: RiskAnalysis
    priority_score: float = Field(ge=0.0, le=1.0)
    rank: int = 0
