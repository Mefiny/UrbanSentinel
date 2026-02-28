"""
TF-IDF + Naive Bayes text classifier for urban risk signals.

Trains on synthetic corpus generated from domain keyword patterns,
providing a real ML classification layer alongside keyword matching.
"""
import re
from typing import List, Tuple, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from backend.models import RiskCategory


# ── Synthetic training corpus ────────────────────────────────
# Each category has template sentences built from domain knowledge.
# This simulates labeled training data without requiring a real dataset.

TRAINING_DATA: Dict[RiskCategory, List[str]] = {
    RiskCategory.crime: [
        "Armed robbery reported at convenience store last night",
        "Police investigating theft at shopping mall parking lot",
        "Domestic violence incident reported in residential area",
        "Gang-related assault near downtown district",
        "Drug trafficking operation busted by local police",
        "Vandalism and property damage at public park",
        "Shoplifting ring targeting electronics stores",
        "Murder investigation underway after body found",
        "Pickpocket gang operating near transit station",
        "Hit-and-run incident leaves pedestrian injured",
        "Burglary at jewelry store during overnight hours",
        "Violent altercation outside nightclub district",
        "Stolen vehicle recovered in abandoned warehouse",
        "Youth gang activity increasing in south district",
        "Armed suspect fled scene after bank holdup",
    ],
    RiskCategory.traffic: [
        "Multi-vehicle collision on expressway causes delays",
        "Traffic gridlock reported on main highway during rush hour",
        "Bus service suspended after brake failure on route",
        "Subway signal malfunction causing commuter delays",
        "Lane closed on bridge due to accident investigation",
        "Pedestrian struck at crosswalk near school zone",
        "Traffic light outage at major intersection",
        "Road construction causing significant detours",
        "Metro line disrupted due to track maintenance",
        "Commuter train delayed after mechanical failure",
        "Highway pileup involving multiple trucks and cars",
        "Expressway ramp closed for emergency repairs",
        "Bicycle lane accident involving delivery rider",
        "Traffic congestion worsening near stadium event",
        "Bus route diverted due to road flooding",
    ],
    RiskCategory.fraud: [
        "Phishing scam targeting residents via fake emails",
        "Cryptocurrency investment fraud reported by retirees",
        "Identity theft ring operating through stolen mail",
        "Fake charity scam soliciting donations door to door",
        "Online shopping fraud with counterfeit products",
        "Ponzi scheme targeting elderly community members",
        "Phone scam impersonating government tax officials",
        "Real estate fraud involving forged property documents",
        "Credit card skimming devices found at ATM machines",
        "Romance scam victims losing life savings online",
        "Fake job offers collecting personal information",
        "Investment fraud promising unrealistic returns",
        "Wire transfer scam targeting small businesses",
        "Insurance fraud ring filing false claims",
        "Counterfeit currency circulating in market district",
    ],
    RiskCategory.infrastructure: [
        "Bridge collapse near downtown area after heavy rain",
        "Power outage affecting thousands of households",
        "Water main burst flooding residential streets",
        "Gas leak detected near elementary school building",
        "Sinkhole opened on major highway after storm",
        "Building crack reported in aging apartment complex",
        "Street light outage creating safety hazard at night",
        "Elevator malfunction trapping residents in tower",
        "Pothole damage causing vehicle accidents on road",
        "Flood warning issued for low-lying river districts",
        "Sewage overflow contaminating local water supply",
        "Electrical fire in aging transformer station",
        "Retaining wall failure threatening hillside homes",
        "Illegal dumping site discovered near water source",
        "Building inspector condemns unsafe structure",
    ],
}


def _preprocess(text: str) -> str:
    """Lowercase and strip non-alphanumeric chars."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class RiskClassifier:
    """TF-IDF + Multinomial Naive Bayes risk category classifier."""

    def __init__(self):
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(
                max_features=500,
                ngram_range=(1, 2),
                stop_words="english",
            )),
            ("clf", MultinomialNB(alpha=0.1)),
        ])
        self._trained = False
        self._train()

    def _train(self):
        """Train on synthetic corpus."""
        texts = []
        labels = []
        for category, samples in TRAINING_DATA.items():
            for sample in samples:
                texts.append(_preprocess(sample))
                labels.append(category.value)
        self.pipeline.fit(texts, labels)
        self._trained = True

    def predict(self, text: str) -> Tuple[RiskCategory, float]:
        """Predict category and confidence for input text."""
        clean = _preprocess(text)
        predicted = self.pipeline.predict([clean])[0]
        proba = self.pipeline.predict_proba([clean])[0]
        confidence = float(max(proba))
        return RiskCategory(predicted), round(confidence, 4)

    def predict_top_n(self, text: str, n: int = 2) -> List[Tuple[RiskCategory, float]]:
        """Return top-n predictions with probabilities."""
        clean = _preprocess(text)
        proba = self.pipeline.predict_proba([clean])[0]
        classes = self.pipeline.classes_
        ranked = sorted(zip(classes, proba), key=lambda x: x[1], reverse=True)
        return [(RiskCategory(c), round(p, 4)) for c, p in ranked[:n]]


# Singleton instance — trained once at import time
_classifier = None


def get_classifier() -> RiskClassifier:
    """Get or create the singleton classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = RiskClassifier()
    return _classifier
