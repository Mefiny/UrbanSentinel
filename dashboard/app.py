import sys
import json
from pathlib import Path

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import Signal, RiskAnalysis, PrioritizedAlert
from backend.analyzer import analyze_signal
from backend.scorer import prioritize_alerts

DATA_PATH = Path(__file__).parent.parent / "data" / "sample_signals.json"

st.set_page_config(
    page_title="UrbanSentinel",
    page_icon="🏙️",
    layout="wide",
)

st.title("UrbanSentinel: AI Public Safety Intelligence")
st.caption("AI-powered urban risk detection, classification, and prioritization")

# ── Load signals ──────────────────────────────────────────────
@st.cache_data
def load_signals() -> list[dict]:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


raw_signals = load_signals()
signals = [Signal(**s) for s in raw_signals]

st.sidebar.header("Controls")
run_analysis = st.sidebar.button("Run AI Analysis", type="primary")
st.sidebar.markdown("---")
st.sidebar.metric("Total Signals", len(signals))

# ── Tabs ──────────────────────────────────────────────────────
tab_overview, tab_alerts, tab_charts = st.tabs(
    ["Signal Overview", "AI Risk Alerts", "Analytics"]
)

# ── Tab 1: Raw signal table ──────────────────────────────────
with tab_overview:
    st.subheader("Raw Public Signals")
    df_signals = pd.DataFrame(raw_signals)
    st.dataframe(df_signals, use_container_width=True, hide_index=True)

# ── Tab 2: AI Risk Alerts ────────────────────────────────────
with tab_alerts:
    st.subheader("AI-Analyzed Risk Alerts")

    if "alerts" not in st.session_state:
        st.session_state.alerts = []

    if run_analysis:
        pairs = []
        progress = st.progress(0, text="Analyzing signals...")
        for i, sig in enumerate(signals):
            try:
                analysis = analyze_signal(sig)
                pairs.append((sig, analysis))
            except Exception as e:
                st.warning(f"Skipped {sig.id}: {e}")
            progress.progress((i + 1) / len(signals), text=f"Analyzed {i+1}/{len(signals)}")
        progress.empty()
        st.session_state.alerts = prioritize_alerts(pairs)
        st.success(f"Analysis complete — {len(pairs)} signals processed")

    alerts: list[PrioritizedAlert] = st.session_state.alerts

    if alerts:
        # Summary metrics row
        col1, col2, col3, col4 = st.columns(4)
        high_risk = sum(1 for a in alerts if a.analysis.risk_level >= 4)
        col1.metric("Total Alerts", len(alerts))
        col2.metric("High Risk (4-5)", high_risk)
        col3.metric("Top Score", f"{alerts[0].priority_score:.2f}")
        col4.metric("Top Category", alerts[0].analysis.category.value)

        st.markdown("---")

        # Alert cards
        for alert in alerts:
            risk = alert.analysis.risk_level
            color = "🔴" if risk >= 4 else "🟡" if risk >= 3 else "🟢"
            with st.expander(
                f"{color} Rank #{alert.rank} — {alert.signal.id} | "
                f"Score: {alert.priority_score:.3f} | "
                f"{alert.analysis.category.value}",
                expanded=(alert.rank <= 3),
            ):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Signal:** {alert.signal.text}")
                    st.markdown(f"**Source:** {alert.signal.source.value}")
                    st.markdown(f"**Location:** {alert.signal.location}")
                with c2:
                    st.markdown(f"**Risk Level:** {risk}/5")
                    st.markdown(f"**Economic Impact:** {alert.analysis.economic_impact.value}")
                    st.markdown(f"**Confidence:** {alert.analysis.confidence:.0%}")
                    st.markdown(f"**Keywords:** {', '.join(alert.analysis.keywords)}")
                st.info(f"**AI Summary:** {alert.analysis.summary}")
    else:
        st.info("Click **Run AI Analysis** in the sidebar to start.")

# ── Tab 3: Analytics ─────────────────────────────────────────
with tab_charts:
    st.subheader("Risk Analytics")

    if not alerts:
        st.info("Run analysis first to see charts.")
    else:
        chart_col1, chart_col2 = st.columns(2)

        # Category distribution pie chart
        with chart_col1:
            st.markdown("#### Risk Category Distribution")
            categories = [a.analysis.category.value for a in alerts]
            cat_counts = pd.Series(categories).value_counts()
            fig1, ax1 = plt.subplots(figsize=(5, 4))
            colors = ["#e74c3c", "#f39c12", "#3498db", "#2ecc71"]
            ax1.pie(
                cat_counts.values,
                labels=cat_counts.index,
                autopct="%1.0f%%",
                colors=colors[: len(cat_counts)],
                startangle=90,
            )
            ax1.set_title("Category Breakdown")
            st.pyplot(fig1)

        # Risk level bar chart
        with chart_col2:
            st.markdown("#### Risk Level Distribution")
            levels = [a.analysis.risk_level for a in alerts]
            level_counts = pd.Series(levels).value_counts().sort_index()
            fig2, ax2 = plt.subplots(figsize=(5, 4))
            bar_colors = ["#2ecc71", "#82e0aa", "#f4d03f", "#e67e22", "#e74c3c"]
            ax2.bar(
                level_counts.index,
                level_counts.values,
                color=[bar_colors[i - 1] for i in level_counts.index],
            )
            ax2.set_xlabel("Risk Level")
            ax2.set_ylabel("Count")
            ax2.set_title("Signals by Risk Level")
            ax2.set_xticks(range(1, 6))
            st.pyplot(fig2)

        st.markdown("---")

        # Location risk heatmap-style bar
        st.markdown("#### Risk Signals by Location")
        locations = [a.signal.location for a in alerts]
        loc_counts = pd.Series(locations).value_counts()
        fig3, ax3 = plt.subplots(figsize=(10, 3))
        ax3.barh(loc_counts.index, loc_counts.values, color="#3498db")
        ax3.set_xlabel("Number of Signals")
        ax3.set_title("Signal Density by District")
        ax3.invert_yaxis()
        st.pyplot(fig3)

        # Top 10 priority scores
        st.markdown("#### Top 10 Priority Alerts")
        top10 = alerts[:10]
        fig4, ax4 = plt.subplots(figsize=(10, 4))
        labels = [f"#{a.rank} {a.signal.id}" for a in top10]
        scores = [a.priority_score for a in top10]
        bar_c = ["#e74c3c" if s > 0.7 else "#f39c12" if s > 0.5 else "#2ecc71" for s in scores]
        ax4.barh(labels[::-1], scores[::-1], color=bar_c[::-1])
        ax4.set_xlabel("Priority Score")
        ax4.set_title("Highest Priority Signals")
        ax4.set_xlim(0, 1)
        st.pyplot(fig4)
