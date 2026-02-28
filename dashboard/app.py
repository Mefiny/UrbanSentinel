import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import Signal, RiskAnalysis, PrioritizedAlert, SourceType, RiskCategory
from backend.analyzer import analyze_signal
from backend.scorer import prioritize_alerts

DATA_PATH = Path(__file__).parent.parent / "data" / "sample_signals.json"

st.set_page_config(
    page_title="UrbanSentinel",
    page_icon="🏙️",
    layout="wide",
)

# ── Custom CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5986 100%);
        padding: 12px 16px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    div[data-testid="stMetric"] label { color: #b0c4de !important; font-size: 0.85rem; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: white !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 20px;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    }
    section[data-testid="stSidebar"] * { color: #e0e0e0; }
    section[data-testid="stSidebar"] .stButton button {
        background: #e74c3c; color: white; border: none; width: 100%;
        font-weight: 700; border-radius: 8px;
    }
    section[data-testid="stSidebar"] .stButton button:hover { background: #c0392b; }
</style>
""", unsafe_allow_html=True)

st.title("🏙️ UrbanSentinel")
st.caption("AI-powered urban risk detection, classification, and prioritization — SDG 11 & 16")

# ── Load signals ──────────────────────────────────────────────
@st.cache_data
def load_signals() -> List[dict]:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


raw_signals = load_signals()
signals = [Signal(**s) for s in raw_signals]

# ── Sidebar ──────────────────────────────────────────────────
st.sidebar.header("⚙️ Controls")
run_analysis = st.sidebar.button("🔍 Run AI Analysis", type="primary")
st.sidebar.markdown("---")
st.sidebar.metric("Total Signals", len(signals))

# Filters
st.sidebar.markdown("---")
st.sidebar.subheader("🔎 Filters")
filter_categories = st.sidebar.multiselect(
    "Risk Category",
    options=[c.value for c in RiskCategory],
    default=[c.value for c in RiskCategory],
)
filter_districts = st.sidebar.multiselect(
    "District",
    options=sorted(set(s["location"] for s in raw_signals)),
    default=sorted(set(s["location"] for s in raw_signals)),
)
filter_risk_min, filter_risk_max = st.sidebar.slider(
    "Risk Level Range", 1, 5, (1, 5)
)

# ── Tabs ──────────────────────────────────────────────────────
tab_overview, tab_alerts, tab_charts, tab_submit = st.tabs(
    ["📋 Signal Overview", "🚨 AI Risk Alerts", "📊 Analytics", "➕ Submit Signal"]
)

# ── Tab 1: Raw signal table ──────────────────────────────────
with tab_overview:
    st.subheader("Raw Public Signals")
    df_signals = pd.DataFrame(raw_signals)
    # Apply district filter to overview too
    df_filtered = df_signals[df_signals["location"].isin(filter_districts)]
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

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

    all_alerts: List[PrioritizedAlert] = st.session_state.alerts

    # Apply filters
    alerts = [
        a for a in all_alerts
        if a.analysis.category.value in filter_categories
        and a.signal.location in filter_districts
        and filter_risk_min <= a.analysis.risk_level <= filter_risk_max
    ]

    if alerts:
        # Summary metrics row
        col1, col2, col3, col4 = st.columns(4)
        high_risk = sum(1 for a in alerts if a.analysis.risk_level >= 4)
        avg_score = sum(a.priority_score for a in alerts) / len(alerts)
        col1.metric("Filtered Alerts", len(alerts))
        col2.metric("High Risk (4-5)", high_risk)
        col3.metric("Avg Score", f"{avg_score:.2f}")
        col4.metric("Top Category", alerts[0].analysis.category.value)

        # CSV export
        export_data = []
        for a in alerts:
            export_data.append({
                "Rank": a.rank, "ID": a.signal.id,
                "Category": a.analysis.category.value,
                "Risk Level": a.analysis.risk_level,
                "Score": round(a.priority_score, 4),
                "Economic Impact": a.analysis.economic_impact.value,
                "Location": a.signal.location,
                "Source": a.signal.source.value,
                "Summary": a.analysis.summary,
            })
        df_export = pd.DataFrame(export_data)
        st.download_button(
            "📥 Export Alerts as CSV",
            df_export.to_csv(index=False).encode("utf-8"),
            file_name="urbansentinel_alerts.csv",
            mime="text/csv",
        )

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
        st.info("Click **🔍 Run AI Analysis** in the sidebar to start.")

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

        # Location risk bar
        st.markdown("#### Risk Signals by Location")
        locations = [a.signal.location for a in alerts]
        loc_counts = pd.Series(locations).value_counts()
        fig3, ax3 = plt.subplots(figsize=(10, 3))
        ax3.barh(loc_counts.index, loc_counts.values, color="#3498db")
        ax3.set_xlabel("Number of Signals")
        ax3.set_title("Signal Density by District")
        ax3.invert_yaxis()
        st.pyplot(fig3)

        # District risk summary table
        st.markdown("#### District Risk Summary")
        district_data = []
        for loc in sorted(set(a.signal.location for a in alerts)):
            loc_alerts = [a for a in alerts if a.signal.location == loc]
            district_data.append({
                "District": loc,
                "Signals": len(loc_alerts),
                "Avg Risk": round(sum(a.analysis.risk_level for a in loc_alerts) / len(loc_alerts), 1),
                "High Risk": sum(1 for a in loc_alerts if a.analysis.risk_level >= 4),
                "Avg Score": round(sum(a.priority_score for a in loc_alerts) / len(loc_alerts), 3),
                "Top Category": pd.Series([a.analysis.category.value for a in loc_alerts]).mode()[0],
            })
        st.dataframe(pd.DataFrame(district_data), use_container_width=True, hide_index=True)

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

# ── Tab 4: Submit Signal ─────────────────────────────────────
with tab_submit:
    st.subheader("Submit a New Signal")
    st.markdown("Simulate submitting a new public signal for AI analysis.")

    with st.form("signal_form"):
        sig_text = st.text_area("Signal Text", placeholder="Describe the incident or observation...")
        fc1, fc2 = st.columns(2)
        with fc1:
            sig_source = st.selectbox("Source Type", [s.value for s in SourceType])
            sig_location = st.text_input("Location", placeholder="e.g. District A")
        with fc2:
            sig_id = st.text_input("Signal ID", value=f"SIG-{len(signals)+1:03d}")
        submitted = st.form_submit_button("🚀 Analyze Signal", type="primary")

    if submitted and sig_text and sig_location:
        new_signal = Signal(
            id=sig_id,
            text=sig_text,
            source=SourceType(sig_source),
            location=sig_location,
            timestamp=datetime.now(),
        )
        result = analyze_signal(new_signal)
        from backend.scorer import compute_priority
        score = compute_priority(new_signal, result)

        st.markdown("---")
        st.markdown("### Analysis Result")
        r1, r2 = st.columns(2)
        with r1:
            st.metric("Category", result.category.value)
            st.metric("Risk Level", f"{result.risk_level}/5")
        with r2:
            st.metric("Economic Impact", result.economic_impact.value)
            st.metric("Priority Score", f"{score:.4f}")
        st.info(f"**AI Summary:** {result.summary}")
        st.markdown(f"**Keywords:** {', '.join(result.keywords)}")
        st.markdown(f"**Confidence:** {result.confidence:.0%}")
    elif submitted:
        st.warning("Please fill in both Signal Text and Location.")

# ── SDG Alignment Footer ─────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; padding: 20px 0; opacity: 0.8;">
    <p style="font-size: 0.95rem; margin-bottom: 4px;">
        🌍 Aligned with <strong>UN SDG 11</strong> (Sustainable Cities) &amp;
        <strong>SDG 16</strong> (Peace, Justice &amp; Strong Institutions)
    </p>
    <p style="font-size: 0.8rem; color: #888;">
        UrbanSentinel — 2026 MEGA Hackathon
    </p>
</div>
""", unsafe_allow_html=True)
