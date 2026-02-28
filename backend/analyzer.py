import re
from typing import List, Tuple
from backend.models import RiskAnalysis, RiskCategory, EconomicImpact, Signal
from backend.ml_classifier import get_classifier


# ── Keyword rules for classification ─────────────────────────
CATEGORY_KEYWORDS = {
    RiskCategory.crime: [
        "robbery", "robber", "theft", "steal", "shoplifting",
        "violence", "assault", "murder", "drug", "vandalism",
        "pickpocket", "gang", "hit-and-run", "domestic violence",
    ],
    RiskCategory.traffic: [
        "traffic", "accident", "pileup", "collision", "gridlock",
        "lane closed", "lane blocked", "delays", "suspended",
        "bus", "subway", "metro", "commuter", "expressway",
        "brake failure", "signal malfunction",
    ],
    RiskCategory.fraud: [
        "scam", "fraud", "phishing", "fake", "identity theft",
        "cryptocurrency", "ponzi", "impersonat",
        "investment fraud",
    ],
    RiskCategory.infrastructure: [
        "collapse", "crack", "sinkhole", "flood", "power outage",
        "water main", "gas leak", "pothole", "bridge",
        "elevator", "street light", "outage", "burst",
        "dumping", "railing", "building inspector",
    ],
}

# Severity escalation keywords
HIGH_SEVERITY = [
    "injur", "killed", "death", "collapse", "armed", "trapped",
    "child", "hospital", "emergency", "critical", "surge",
    "12,000", "thousands", "$2M", "flood warning",
]
MEDIUM_SEVERITY = [
    "closed", "blocked", "suspended", "multiple", "increased",
    "malfunction", "failure", "outage", "damage", "hazard",
]


def _match_category(text: str) -> Tuple[RiskCategory, List[str]]:
    """Match text against keyword rules, return category and matched keywords."""
    text_lower = text.lower()
    best_cat = RiskCategory.infrastructure
    best_score = 0
    matched_kw: List[str] = []

    for cat, keywords in CATEGORY_KEYWORDS.items():
        hits = [kw for kw in keywords if kw in text_lower]
        if len(hits) > best_score:
            best_score = len(hits)
            best_cat = cat
            matched_kw = hits

    return best_cat, matched_kw[:5]


def _assess_severity(text: str) -> Tuple[int, EconomicImpact]:
    """Assess risk level (1-5) and economic impact from text."""
    text_lower = text.lower()
    high_hits = sum(1 for kw in HIGH_SEVERITY if kw in text_lower)
    med_hits = sum(1 for kw in MEDIUM_SEVERITY if kw in text_lower)

    if high_hits >= 2:
        return 5, EconomicImpact.high
    elif high_hits == 1:
        return 4, EconomicImpact.high
    elif med_hits >= 2:
        return 3, EconomicImpact.medium
    elif med_hits == 1:
        return 2, EconomicImpact.medium
    return 1, EconomicImpact.low


def _hybrid_classify(text: str) -> Tuple[RiskCategory, List[str], float]:
    """Combine keyword matching (60%) with ML prediction (40%) for classification."""
    kw_category, keywords = _match_category(text)
    kw_confidence = min(0.95, 0.5 + len(keywords) * 0.1)

    clf = get_classifier()
    ml_category, ml_confidence = clf.predict(text)

    # If both agree, boost confidence
    if kw_category == ml_category:
        final_category = kw_category
        final_confidence = min(0.95, kw_confidence * 0.6 + ml_confidence * 0.4 + 0.05)
    elif len(keywords) >= 2:
        # Strong keyword match wins
        final_category = kw_category
        final_confidence = kw_confidence * 0.7 + ml_confidence * 0.3
    elif ml_confidence > 0.6:
        # ML is confident and keywords are weak
        final_category = ml_category
        final_confidence = ml_confidence * 0.6 + kw_confidence * 0.4
    else:
        # Default to keyword result
        final_category = kw_category
        final_confidence = kw_confidence * 0.6 + ml_confidence * 0.4

    return final_category, keywords, round(min(final_confidence, 0.95), 2)


def analyze_signal(signal: Signal) -> RiskAnalysis:
    """Analyze a signal using hybrid keyword + ML classification."""
    text = signal.text
    category, keywords, confidence = _hybrid_classify(text)
    risk_level, economic_impact = _assess_severity(text)

    # Generate summary from first sentence
    first_sentence = text.split(".")[0].strip()
    summary = f"{category.value} risk detected: {first_sentence}."

    return RiskAnalysis(
        category=category,
        risk_level=risk_level,
        economic_impact=economic_impact,
        confidence=confidence,
        keywords=keywords if keywords else [category.value.lower()],
        summary=summary,
    )
