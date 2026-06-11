import pandas as pd
import plotly.express as px
import streamlit as st

from constants import RISK_HEATMAP_COLUMNS

CUSTOM_CSS = """
<style>
    .stApp {background: linear-gradient(180deg, #f7f9fc 0%, #edf2f7 48%, #f8fafc 100%);}
    .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1480px;}
    .hero-wrap {background: radial-gradient(circle at top left, rgba(148,163,184,0.18), transparent 24%), linear-gradient(135deg, #0f172a 0%, #15345b 52%, #1e3a5f 100%); border-radius: 28px; padding: 34px 34px 28px 34px; color: white; box-shadow: 0 18px 50px rgba(15,23,42,0.18); margin-bottom: 18px; border: 1px solid rgba(255,255,255,0.06);}
    .hero-kicker {font-size: 0.82rem; letter-spacing: .12em; text-transform: uppercase; color: #bfdbfe; margin-bottom: 8px; font-weight: 700;}
    .hero-title {font-size: 2.15rem; font-weight: 900; margin-bottom: 10px;}
    .hero-subtitle {font-size: 1rem; opacity: 0.96; line-height: 1.72; max-width: 1080px;}
    .info-chip-row {display:flex; gap:10px; flex-wrap:wrap; margin-top:18px;}
    .info-chip {background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18); padding: 8px 12px; border-radius: 999px; font-size: 0.9rem; backdrop-filter: blur(8px);}
    .metric-card {background: rgba(255,255,255,0.92); border:1px solid rgba(148,163,184,0.20); border-radius:20px; padding:20px 22px; box-shadow:0 12px 32px rgba(15,23,42,0.08); min-height: 138px;}
    .metric-label {color:#64748b; font-size:0.88rem; margin-bottom:6px; font-weight:600;}
    .metric-value {font-size:1.9rem; font-weight:900; color:#0f172a; line-height:1.15;}
    .metric-caption {font-size:0.87rem; color:#475569; margin-top:8px; line-height: 1.55;}
    .metric-badge {display:inline-block; margin-top:10px; background:#eff6ff; color:#1d4ed8; font-size:0.76rem; padding:5px 9px; border-radius:999px; font-weight:700;}
    .section-card {background:rgba(255,255,255,0.94); border:1px solid rgba(148,163,184,0.22); border-radius:22px; padding:18px 18px 14px 18px; box-shadow:0 10px 28px rgba(15,23,42,0.06); margin-bottom:16px;}
    .small-title {font-size:1.03rem; font-weight:800; color:#0f172a; margin-bottom:10px;}
    .section-subtitle {font-size:0.85rem; color:#64748b; margin-bottom:14px;}
    .alert-high,.alert-medium,.alert-low {border-radius:16px; padding:14px 16px; margin-bottom:10px; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.7);}
    .alert-high {border-left:6px solid #ef4444; background:linear-gradient(90deg, #fff5f5, #fffafb);}
    .alert-medium {border-left:6px solid #f59e0b; background:linear-gradient(90deg, #fffaf0, #fffdf7);}
    .alert-low {border-left:6px solid #10b981; background:linear-gradient(90deg, #f0fdf4, #f7fffb);}
    .alert-title {font-weight:800; color:#0f172a; margin-bottom:4px;}
    .alert-detail {color:#334155; font-size:0.92rem; line-height:1.56;}
    .summary-good {border-left:6px solid #10b981; background:#f0fdf4; border-radius:16px; padding:14px 16px; margin-bottom:12px;}
    .summary-bad {border-left:6px solid #ef4444; background:#fff7f7; border-radius:16px; padding:14px 16px; margin-bottom:12px;}
    .premium-note {background: linear-gradient(135deg, #eff6ff, #f8fafc); border:1px solid #dbeafe; border-radius:18px; padding:16px 18px; color:#1e3a8a;}
    .report-box textarea {font-size:0.95rem !important; line-height:1.6 !important;}
    .demo-banner {background: linear-gradient(90deg, #dbeafe, #eff6ff); border:1px solid #bfdbfe; border-radius:16px; padding:14px 18px; margin-bottom:18px; color:#1e3a8a;}
    .status-banner {background: linear-gradient(90deg, #ecfeff, #f8fafc); border:1px solid #bae6fd; border-radius:16px; padding:14px 18px; margin-bottom:18px; color:#0f172a;}
    .status-chip-row {display:flex; gap:10px; flex-wrap:wrap; margin-top:10px;}
    .status-chip {background:#ffffff; border:1px solid #dbeafe; padding:7px 10px; border-radius:999px; font-size:0.84rem; color:#0f172a;}
    .sidebar-card {background:rgba(255,255,255,0.78); border:1px solid rgba(148,163,184,0.18); border-radius:18px; padding:14px 14px 10px 14px; margin:10px 0 14px 0;}
    .sidebar-kpi {font-size:0.83rem; color:#475569; line-height:1.65;}
    .sidebar-kpi b {color:#0f172a;}
    div[data-testid="stTabs"] button[role="tab"] {font-weight: 700; border-radius: 999px; padding: 10px 18px;}
    div[data-testid="stTabs"] button[aria-selected="true"] {background: linear-gradient(90deg, #dbeafe, #eff6ff); color: #1d4ed8;}
</style>
"""


def inject_custom_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def metric_card(label: str, value: str, caption: str = "", badge: str = ""):
    badge_html = f'<div class="metric-badge">{badge}</div>' if badge else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-caption">{caption}</div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alert_card(row):
    severity_class = {"High": "alert-high", "Medium": "alert-medium", "Low": "alert-low"}.get(row["severity"], "alert-low")
    st.markdown(
        f"""
        <div class="{severity_class}">
            <div class="alert-title">[{row['severity']}] {row['company_name']} · {row['alert_type']}</div>
            <div class="alert-detail">{row['detail']}</div>
            <div class="alert-detail" style="margin-top:6px;"><b>권고 조치</b> · {row['recommended_action']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_reason_box(title: str, content: str, positive: bool = True):
    css_class = "summary-good" if positive else "summary-bad"
    st.markdown(
        f"""
        <div class="{css_class}">
            <div class="alert-title">{title}</div>
            <div class="alert-detail">{content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_risk_heatmap_figure(risk_df: pd.DataFrame):
    if risk_df is None or risk_df.empty:
        return None
    missing = [col for col in RISK_HEATMAP_COLUMNS if col not in risk_df.columns]
    if missing:
        return None
    heatmap_df = risk_df[["company_name", *RISK_HEATMAP_COLUMNS.keys()]].copy().rename(columns=RISK_HEATMAP_COLUMNS)
    heatmap_df = heatmap_df.set_index("company_name")
    fig = px.imshow(
        heatmap_df,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        labels={"x": "리스크 축", "y": "계열사", "color": "점수"},
    )
    fig.update_layout(height=340, margin=dict(l=0, r=0, t=24, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig
