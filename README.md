# UrbanSentinel: AI Public Safety Intelligence

An AI-powered urban risk detection, classification, and prioritization system built for the **2026 MEGA Hackathon**.

Aligned with **UN SDG 11** (Sustainable Cities and Communities) and **SDG 16** (Peace, Justice and Strong Institutions).

---

## Problem

Cities generate massive volumes of public signals daily — news, citizen reports, social media, government alerts. Institutions struggle to process these efficiently. Critical warnings get buried in noise, delaying response and eroding public trust.

## Solution

UrbanSentinel transforms unstructured public signals into **prioritized, actionable intelligence** using AI-driven risk analysis.

The system:
- Aggregates multi-source public text signals (news, citizen reports, social media, government)
- Supports **multi-language input** (English and Chinese) with automatic language detection
- Uses a **hybrid ML + keyword NLP engine** to extract structured risk metadata (category, severity, economic impact)
- Computes weighted priority scores for institutional decision support
- Provides **anomaly trend prediction** with time-series forecasting
- Fetches **real-time news** via GNews API for live risk monitoring
- Visualizes risk distribution via an interactive dashboard with **geospatial risk maps**

---

## Architecture

```
Public Signals (news / reports / social / government)
        │
        ▼
   FastAPI Backend
        │
        ▼
  ┌─────────────────────────┐
  │  Hybrid NLP Classifier  │
  │  ┌───────┐ ┌─────────┐  │
  │  │Keyword│ │ TF-IDF  │  │
  │  │ Rules │ │+ NaiveBa│  │
  │  │ (60%) │ │yes(40%) │  │
  │  └───┬───┘ └────┬────┘  │
  │      └─────┬────┘       │
  │         Fusion          │
  └────────────┬────────────┘
               ▼
  Structured JSON output
  (category, risk_level, economic_impact,
   confidence, keywords, summary)
               ▼
  Priority Scoring Engine
        │
        │  Score = 0.4×Risk + 0.3×Economic + 0.2×Credibility + 0.1×Recency
        ▼
  Streamlit Dashboard ──► Ranked alerts, charts, district analysis
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python, FastAPI |
| AI Engine | TF-IDF + Naive Bayes + Keyword Rules (hybrid) |
| ML Framework | scikit-learn |
| Language Detection | Regex-based CJK detection (EN/ZH) |
| Trend Prediction | NumPy polynomial fitting + forecasting |
| Geospatial Maps | Folium + streamlit-folium |
| News API | GNews API + httpx |
| Scoring | Custom weighted priority algorithm |
| Dashboard | Streamlit |
| Data Processing | Pandas |
| Visualization | Matplotlib |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Dashboard

```bash
streamlit run dashboard/app.py
```

### 3. Run the API (optional)

```bash
uvicorn backend.main:app --reload
```

---

## Testing

75 unit tests covering all core modules:

```bash
pytest tests/ -v
```

```
tests/test_analyzer.py       — 23 tests (category matching, severity, hybrid pipeline, Chinese signals)
tests/test_language.py       — 10 tests (language detection, Chinese keyword matching)
tests/test_news_fetcher.py   — 14 tests (article conversion, API fetch, country filter, aggregation)
tests/test_ml_classifier.py  — 10 tests (TF-IDF prediction, preprocessing, confidence)
tests/test_scorer.py         — 12 tests (recency weight, priority computation, ranking)
tests/test_models.py         —  6 tests (Pydantic validation, boundary checks)

============================== 75 passed ==============================
```

---

## Priority Scoring Algorithm

Each signal receives a weighted priority score:

```
Priority Score = 0.4 × Risk Level + 0.3 × Economic Impact + 0.2 × Source Credibility + 0.1 × Recency
```

| Factor | Weight | Description |
|--------|--------|-------------|
| Risk Level | 0.4 | AI-assessed severity (1-5, normalized) |
| Economic Impact | 0.3 | Estimated financial consequence (Low/Medium/High) |
| Source Credibility | 0.2 | Government > News > Citizen > Social Media |
| Recency | 0.1 | More recent signals weighted higher |

---

## Innovation

- **Hybrid AI classification** — combines TF-IDF + Naive Bayes ML model with keyword rules for robust, explainable predictions
- **Multi-language risk detection** — automatic language detection with Chinese keyword classification support
- **Anomaly trend prediction** — time-series analysis with polynomial trend fitting and short-term forecasting
- **Real-time news integration** — live news fetching via GNews API with automatic signal conversion
- **Geospatial risk mapping** — interactive Folium maps with category-coded markers and district overlays
- Goes beyond text classification — builds a **decision-support system**
- Converts qualitative risk narratives into **quantifiable indicators**
- Explainable scoring model (not a black box)
- Lightweight, deployable in low-resource municipal environments

---

## SDG Alignment

| Goal | How UrbanSentinel Contributes |
|------|-------------------------------|
| **SDG 11** — Sustainable Cities | Enhances urban resilience through early risk detection and response prioritization |
| **SDG 16** — Strong Institutions | Strengthens institutional decision-making capacity with data-driven intelligence |

---

## Project Structure

```
UrbanSentinel/
├── backend/
│   ├── __init__.py
│   ├── main.py            # FastAPI application
│   ├── models.py           # Pydantic data schemas
│   ├── analyzer.py         # Hybrid keyword + ML classifier
│   ├── ml_classifier.py    # TF-IDF + Naive Bayes pipeline
│   ├── language.py         # Multi-language detection (EN/ZH)
│   ├── news_fetcher.py     # GNews real-time news integration
│   └── scorer.py           # Priority scoring algorithm
├── dashboard/
│   └── app.py            # Streamlit visualization
├── data/
│   └── sample_signals.json # 35 signals (EN + ZH)
├── tests/
│   ├── conftest.py            # Test configuration
│   ├── test_analyzer.py       # 23 tests
│   ├── test_language.py       # 10 tests
│   ├── test_news_fetcher.py   # 11 tests
│   ├── test_ml_classifier.py  # 10 tests
│   ├── test_scorer.py         # 12 tests
│   └── test_models.py         #  6 tests
├── config.py
├── requirements.txt
└── README.md
```

---

## Use Cases

- Municipal emergency management departments
- Community-level governance and safety monitoring
- Traffic management centers
- Public safety early warning systems

---

## Future Work

- Extended multi-language support (Japanese, Korean, Arabic, etc.)
- Deep learning anomaly detection models
- Integration with city IoT sensor data
- Push notification alerts for high-risk events
- Historical trend comparison and seasonal pattern analysis

---

## License

MIT
