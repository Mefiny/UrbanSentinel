from datetime import datetime, timezone
from typing import List, Tuple
from backend.models import Signal, RiskAnalysis, PrioritizedAlert, EconomicImpact
from config import W_RISK, W_ECONOMIC, W_CREDIBILITY, W_RECENCY, SOURCE_CREDIBILITY


ECONOMIC_WEIGHT_MAP = {
    EconomicImpact.low: 0.2,
    EconomicImpact.medium: 0.5,
    EconomicImpact.high: 1.0,
}


def _recency_weight(timestamp: datetime) -> float:
    """More recent signals get higher weight (0-1 scale)."""
    now = datetime.now(timezone.utc)
    ts = timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp
    hours_ago = (now - ts).total_seconds() / 3600
    if hours_ago <= 1:
        return 1.0
    elif hours_ago <= 6:
        return 0.8
    elif hours_ago <= 24:
        return 0.5
    elif hours_ago <= 72:
        return 0.3
    return 0.1


def compute_priority(signal: Signal, analysis: RiskAnalysis) -> float:
    """Compute priority score (0-1) using weighted formula."""
    r = analysis.risk_level / 5.0
    e = ECONOMIC_WEIGHT_MAP[analysis.economic_impact]
    c = SOURCE_CREDIBILITY.get(signal.source.value, 0.5)
    t = _recency_weight(signal.timestamp)

    score = W_RISK * r + W_ECONOMIC * e + W_CREDIBILITY * c + W_RECENCY * t
    return round(min(score, 1.0), 4)


def prioritize_alerts(
    pairs: List[Tuple[Signal, RiskAnalysis]],
) -> List[PrioritizedAlert]:
    """Score and rank a list of (signal, analysis) pairs."""
    alerts = []
    for signal, analysis in pairs:
        score = compute_priority(signal, analysis)
        alerts.append(
            PrioritizedAlert(
                signal=signal,
                analysis=analysis,
                priority_score=score,
            )
        )
    alerts.sort(key=lambda a: a.priority_score, reverse=True)
    for i, alert in enumerate(alerts):
        alert.rank = i + 1
    return alerts
