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
- Uses LLMs to extract structured risk metadata (category, severity, economic impact)
- Computes weighted priority scores for institutional decision support
- Visualizes risk distribution via an interactive dashboard

---

## Architecture

```
Public Signals (news / reports / social / government)
        │
        ▼
   FastAPI Backend
        │
        ▼
  NLP Risk Classifier ──► Structured JSON output
        │                 (category, risk_level, economic_impact,
        │                  confidence, keywords, summary)
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
| AI Engine | Keyword-based NLP Risk Classifier |
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

36 unit tests covering all core modules:

```bash
pytest tests/ -v
```

```
tests/test_analyzer.py  — 18 tests (category matching, severity assessment, full pipeline)
tests/test_scorer.py    — 12 tests (recency weight, priority computation, ranking)
tests/test_models.py    —  6 tests (Pydantic validation, boundary checks)

============================== 36 passed ==============================
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
│   ├── main.py          # FastAPI application
│   ├── models.py         # Pydantic data schemas
│   ├── analyzer.py       # NLP risk classifier
│   └── scorer.py         # Priority scoring algorithm
├── dashboard/
│   └── app.py            # Streamlit visualization
├── data/
│   └── sample_signals.json
├── tests/
│   ├── conftest.py        # Test configuration
│   ├── test_analyzer.py   # 18 tests — category matching, severity, integration
│   ├── test_scorer.py     # 12 tests — priority scoring, recency, ranking
│   └── test_models.py     #  6 tests — Pydantic validation
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

- Real-time news API integration
- Geospatial visualization with interactive maps
- Multi-language risk detection
- Anomaly trend prediction models
- Integration with city IoT sensor data

---

## License

MIT
