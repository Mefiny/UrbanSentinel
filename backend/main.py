import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models import Signal, PrioritizedAlert
from backend.analyzer import analyze_signal
from backend.scorer import prioritize_alerts

app = FastAPI(
    title="UrbanSentinel API",
    description="AI-powered urban risk intelligence",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).parent.parent / "data" / "sample_signals.json"


def _load_signals() -> list[Signal]:
    with open(DATA_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return [Signal(**item) for item in raw]


@app.get("/signals", response_model=list[Signal])
def get_signals():
    """Return all raw signals."""
    return _load_signals()


@app.post("/analyze", response_model=PrioritizedAlert)
def analyze_single(signal: Signal):
    """Analyze a single signal and return scored alert."""
    try:
        analysis = analyze_signal(signal)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    from backend.scorer import compute_priority
    score = compute_priority(signal, analysis)
    return PrioritizedAlert(
        signal=signal, analysis=analysis, priority_score=score, rank=0
    )


@app.post("/analyze/batch", response_model=list[PrioritizedAlert])
def analyze_batch():
    """Analyze all sample signals and return ranked alerts."""
    signals = _load_signals()
    pairs = []
    for sig in signals:
        try:
            analysis = analyze_signal(sig)
            pairs.append((sig, analysis))
        except Exception:
            continue
    return prioritize_alerts(pairs)


@app.get("/health")
def health():
    return {"status": "ok", "service": "UrbanSentinel"}
