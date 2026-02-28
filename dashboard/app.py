import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List

import numpy as np
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import folium
from streamlit_folium import st_folium

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.models import Signal, RiskAnalysis, PrioritizedAlert, SourceType, RiskCategory
from backend.analyzer import analyze_signal
from backend.scorer import prioritize_alerts
from config import DISTRICT_COORDS

DATA_PATH = Path(__file__).parent.parent / "data" / "sample_signals.json"

st.set_page_config(
    page_title="UrbanSentinel",
    page_icon="US",
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

st.title("UrbanSentinel")
st.caption("AI-powered urban risk detection, classification, and prioritization — SDG 11 & 16")

# ── Load signals ──────────────────────────────────────────────
@st.cache_data
def load_signals() -> List[dict]:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


raw_signals = load_signals()
signals = [Signal(**s) for s in raw_signals]

# ── Sidebar ──────────────────────────────────────────────────
st.sidebar.header("Controls")
run_analysis = st.sidebar.button("Run AI Analysis", type="primary")
st.sidebar.markdown("---")
st.sidebar.metric("Total Signals", len(signals))

# Filters
st.sidebar.markdown("---")
st.sidebar.subheader("Filters")
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
tab_overview, tab_alerts, tab_charts, tab_map, tab_submit = st.tabs(
    ["Signal Overview", "AI Risk Alerts", "Analytics", "Risk Map", "Submit Signal"]
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
            "Export Alerts as CSV",
            df_export.to_csv(index=False).encode("utf-8"),
            file_name="urbansentinel_alerts.csv",
            mime="text/csv",
        )

        st.markdown("---")

        # Alert cards
        for alert in alerts:
            risk = alert.analysis.risk_level
            color = "[!]" if risk >= 4 else "[~]" if risk >= 3 else "[o]"
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

# ── Chart style helper ───────────────────────────────────────
_BG = "#0e1117"
_FG = "#c8d0d8"
_GRID = "#1e2a38"
_PALETTE = {
    "crime": "#ef4444", "traffic": "#f59e0b",
    "fraud": "#8b5cf6", "infrastructure": "#3b82f6",
}
_RISK_COLORS = ["#22c55e", "#84cc16", "#eab308", "#f97316", "#ef4444"]


def _dark_fig(w=6, h=4):
    fig, ax = plt.subplots(figsize=(w, h), facecolor=_BG)
    ax.set_facecolor(_BG)
    ax.tick_params(colors=_FG, labelsize=9)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return fig, ax


# ── Tab 3: Analytics ─────────────────────────────────────────
with tab_charts:
    st.subheader("Risk Analytics")

    if not alerts:
        st.info("Run analysis first to see charts.")
    else:
        chart_col1, chart_col2 = st.columns(2)

        # ── Donut chart: category distribution ───────────────
        with chart_col1:
            st.markdown("#### Category Distribution")
            categories = [a.analysis.category.value for a in alerts]
            cat_counts = pd.Series(categories).value_counts()
            cat_colors = [_PALETTE.get(c.lower().split()[0], "#64748b")
                          for c in cat_counts.index]

            fig1, ax1 = plt.subplots(figsize=(5, 4.5), facecolor=_BG)
            ax1.set_facecolor(_BG)
            wedges, texts, autotexts = ax1.pie(
                cat_counts.values,
                labels=cat_counts.index,
                autopct="%1.0f%%",
                colors=cat_colors,
                startangle=90,
                pctdistance=0.78,
                wedgeprops=dict(width=0.45, edgecolor=_BG, linewidth=2),
            )
            for t in texts:
                t.set_color(_FG)
                t.set_fontsize(9)
            for t in autotexts:
                t.set_color("white")
                t.set_fontsize(10)
                t.set_fontweight("bold")
            centre = plt.Circle((0, 0), 0.35, fc=_BG)
            ax1.add_artist(centre)
            ax1.text(0, 0, str(len(alerts)), ha="center", va="center",
                     fontsize=22, fontweight="bold", color="white")
            ax1.text(0, -0.12, "signals", ha="center", va="center",
                     fontsize=9, color=_FG)
            st.pyplot(fig1)

        # ── Risk level bar chart ─────────────────────────────
        with chart_col2:
            st.markdown("#### Risk Level Distribution")
            levels = [a.analysis.risk_level for a in alerts]
            level_counts = pd.Series(levels).value_counts().reindex(
                range(1, 6), fill_value=0
            )

            fig2, ax2 = _dark_fig(5, 4.5)
            bars = ax2.bar(
                level_counts.index, level_counts.values,
                color=[_RISK_COLORS[i - 1] for i in level_counts.index],
                width=0.6, edgecolor=_BG, linewidth=1.5,
                zorder=3,
            )
            for bar in bars:
                h = bar.get_height()
                if h > 0:
                    ax2.text(bar.get_x() + bar.get_width() / 2, h + 0.15,
                             str(int(h)), ha="center", va="bottom",
                             color="white", fontsize=11, fontweight="bold")
            ax2.set_xlabel("Risk Level", color=_FG, fontsize=10)
            ax2.set_ylabel("Count", color=_FG, fontsize=10)
            ax2.set_xticks(range(1, 6))
            ax2.set_xticklabels(["1\nLow", "2", "3\nMed", "4", "5\nHigh"],
                                fontsize=8, color=_FG)
            ax2.yaxis.grid(True, color=_GRID, linewidth=0.5, zorder=0)
            ax2.set_axisbelow(True)
            st.pyplot(fig2)

        st.markdown("---")

        # ── Location horizontal bar ──────────────────────────
        st.markdown("#### Signal Density by District")
        locations = [a.signal.location for a in alerts]
        loc_counts = pd.Series(locations).value_counts()

        fig3, ax3 = _dark_fig(10, max(2.5, len(loc_counts) * 0.45))
        y_pos = range(len(loc_counts))
        ax3.barh(y_pos, loc_counts.values,
                 color="#3b82f6", height=0.55, edgecolor=_BG,
                 linewidth=1, zorder=3)
        for i, v in enumerate(loc_counts.values):
            ax3.text(v + 0.1, i, str(v), va="center",
                     color="white", fontsize=10, fontweight="bold")
        ax3.set_yticks(y_pos)
        ax3.set_yticklabels(loc_counts.index, color=_FG, fontsize=9)
        ax3.invert_yaxis()
        ax3.xaxis.grid(True, color=_GRID, linewidth=0.5, zorder=0)
        ax3.set_axisbelow(True)
        ax3.set_xlabel("Number of Signals", color=_FG, fontsize=10)
        st.pyplot(fig3)

        st.markdown("---")

        # ── District risk summary table ──────────────────────
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

        st.markdown("---")

        # ── Top 10 priority scores ───────────────────────────
        st.markdown("#### Top 10 Priority Alerts")
        top10 = alerts[:10]
        fig4, ax4 = _dark_fig(10, max(3, len(top10) * 0.45))
        labels = [f"#{a.rank}  {a.signal.id}" for a in top10]
        scores = [a.priority_score for a in top10]
        bar_c = ["#ef4444" if s > 0.7 else "#f59e0b" if s > 0.5 else "#22c55e"
                 for s in scores]
        ax4.barh(labels[::-1], scores[::-1], color=bar_c[::-1],
                 height=0.55, edgecolor=_BG, linewidth=1, zorder=3)
        for i, s in enumerate(scores[::-1]):
            ax4.text(s + 0.01, i, f"{s:.3f}", va="center",
                     color="white", fontsize=9, fontweight="bold")
        ax4.set_xlabel("Priority Score", color=_FG, fontsize=10)
        ax4.set_xlim(0, 1.05)
        ax4.xaxis.grid(True, color=_GRID, linewidth=0.5, zorder=0)
        ax4.set_axisbelow(True)
        ax4.tick_params(axis="y", labelsize=9, colors=_FG)
        st.pyplot(fig4)

        st.markdown("---")

        # ── Signal Timeline & Trend Prediction ─────────────
        st.markdown("#### Signal Timeline & Anomaly Trend")
        timestamps = [a.signal.timestamp for a in alerts]
        ts_series = pd.Series(timestamps)
        ts_hours = ts_series.dt.floor("h")
        hourly_counts = ts_hours.value_counts().sort_index()

        fig5, ax5 = _dark_fig(10, 4)
        x_dates = hourly_counts.index.to_pydatetime()
        y_vals = hourly_counts.values

        # Actual signal counts
        ax5.bar(x_dates, y_vals, width=0.03, color="#3b82f6",
                edgecolor=_BG, linewidth=1, zorder=3, label="Signals/hour")

        # Trend line using polynomial fit
        if len(x_dates) >= 3:
            x_num = np.arange(len(x_dates))
            coeffs = np.polyfit(x_num, y_vals, deg=min(2, len(x_dates) - 1))
            trend = np.polyval(coeffs, x_num)
            ax5.plot(x_dates, trend, color="#f59e0b", linewidth=2.5,
                     linestyle="--", zorder=4, label="Trend")

            # Forecast next 3 hours
            future_x = np.arange(len(x_dates), len(x_dates) + 3)
            future_y = np.polyval(coeffs, future_x)
            future_y = np.clip(future_y, 0, None)
            last_dt = x_dates[-1]
            future_dates = [last_dt + pd.Timedelta(hours=i+1) for i in range(3)]
            ax5.plot(future_dates, future_y, color="#ef4444", linewidth=2.5,
                     linestyle=":", zorder=4, label="Forecast")
            ax5.scatter(future_dates, future_y, color="#ef4444",
                        s=40, zorder=5, edgecolors="white", linewidths=0.8)

        ax5.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax5.tick_params(axis="x", rotation=45, colors=_FG, labelsize=8)
        ax5.set_xlabel("Time", color=_FG, fontsize=10)
        ax5.set_ylabel("Signal Count", color=_FG, fontsize=10)
        ax5.yaxis.grid(True, color=_GRID, linewidth=0.5, zorder=0)
        ax5.set_axisbelow(True)
        ax5.legend(facecolor=_BG, edgecolor=_GRID, labelcolor=_FG,
                   fontsize=8, loc="upper left")
        fig5.tight_layout()
        st.pyplot(fig5)

# ── Tab 4: Risk Map ───────────────────────────────────────────
with tab_map:
    st.subheader("Geospatial Risk Map")

    if not alerts:
        st.info("Run analysis first to see the risk map.")
    else:
        # Build folium map centered on Shanghai
        center_lat = sum(c[0] for c in DISTRICT_COORDS.values()) / len(DISTRICT_COORDS)
        center_lon = sum(c[1] for c in DISTRICT_COORDS.values()) / len(DISTRICT_COORDS)
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13,
                       tiles="CartoDB dark_matter")

        # Color by risk category
        cat_colors = {
            "Crime": "red", "Traffic": "orange",
            "Fraud": "purple", "Infrastructure Failure": "blue",
        }
        risk_icons = {1: "info-sign", 2: "info-sign", 3: "warning-sign",
                      4: "exclamation-sign", 5: "fire"}

        for alert in alerts:
            loc = alert.signal.location
            if loc not in DISTRICT_COORDS:
                continue
            lat, lon = DISTRICT_COORDS[loc]
            # Add small random offset so markers don't stack
            import random
            random.seed(hash(alert.signal.id))
            lat += random.uniform(-0.003, 0.003)
            lon += random.uniform(-0.003, 0.003)

            cat = alert.analysis.category.value
            risk = alert.analysis.risk_level
            color = cat_colors.get(cat, "gray")

            popup_html = (
                f"<b>{alert.signal.id}</b><br>"
                f"<b>Category:</b> {cat}<br>"
                f"<b>Risk:</b> {risk}/5<br>"
                f"<b>Score:</b> {alert.priority_score:.3f}<br>"
                f"<b>Location:</b> {loc}<br>"
                f"<small>{alert.signal.text[:80]}...</small>"
            )

            folium.CircleMarker(
                location=[lat, lon],
                radius=6 + risk * 3,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=f"{alert.signal.id} | {cat} | Risk {risk}",
            ).add_to(m)

        # District labels
        for name, (lat, lon) in DISTRICT_COORDS.items():
            folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(html=f'<div style="font-size:11px;color:#fff;'
                                         f'font-weight:bold;text-shadow:1px 1px 2px #000">'
                                         f'{name}</div>'),
            ).add_to(m)

        st_folium(m, use_container_width=True, height=520)

        # Legend
        st.markdown(
            '<div style="display:flex;gap:16px;justify-content:center;padding:8px 0">'
            '<span style="color:#ef4444">&#9679; Crime</span>'
            '<span style="color:#f59e0b">&#9679; Traffic</span>'
            '<span style="color:#8b5cf6">&#9679; Fraud</span>'
            '<span style="color:#3b82f6">&#9679; Infrastructure</span>'
            '</div>',
            unsafe_allow_html=True,
        )

# ── Tab 5: Submit Signal ─────────────────────────────────────
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
        submitted = st.form_submit_button("Analyze Signal", type="primary")

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
        Aligned with <strong>UN SDG 11</strong> (Sustainable Cities) &amp;
        <strong>SDG 16</strong> (Peace, Justice &amp; Strong Institutions)
    </p>
    <p style="font-size: 0.8rem; color: #888;">
        UrbanSentinel — 2026 MEGA Hackathon
    </p>
</div>
""", unsafe_allow_html=True)
