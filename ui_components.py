import html

import pandas as pd
import plotly.express as px
import streamlit as st

from constants import RISK_HEATMAP_COLUMNS

CHART_COLORS = ["#1d4ed8", "#3b82f6", "#93c5fd", "#dc2626", "#f59e0b"]

CUSTOM_CSS = """
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [class*="css"], .stApp, .stMarkdown, .stTextInput, .stSelectbox, .stRadio, .stButton button, .stDataFrame {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    .stApp {background: linear-gradient(180deg, #f5f7fb 0%, #eef2f7 45%, #f8fafc 100%);}
    .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1480px;}
    .hero-wrap {background: radial-gradient(circle at top left, rgba(191,219,254,0.16), transparent 26%), linear-gradient(135deg, #0f172a 0%, #173a63 52%, #1d4f83 100%); border-radius: 28px; padding: 34px 34px 28px 34px; color: white; box-shadow: 0 18px 50px rgba(15,23,42,0.18); margin-bottom: 18px; border: 1px solid rgba(255,255,255,0.06);}
    .hero-kicker {font-size: 0.82rem; letter-spacing: .12em; text-transform: uppercase; color: #bfdbfe; margin-bottom: 8px; font-weight: 700;}
    .hero-title {font-size: 2.15rem; font-weight: 900; margin-bottom: 10px;}
    .hero-subtitle {font-size: 1rem; opacity: 0.96; line-height: 1.72; max-width: 1080px;}
    .info-chip-row {display:flex; gap:10px; flex-wrap:wrap; margin-top:18px;}
    .info-chip {background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18); padding: 8px 12px; border-radius: 999px; font-size: 0.9rem; backdrop-filter: blur(8px);}
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .metric-card {background: #ffffff; border:1px solid #e2e8f0; border-radius:18px; padding:18px 20px; box-shadow:0 10px 28px rgba(15,23,42,0.06); min-height: 136px; animation: fadeUp 0.28s ease;}
    .metric-label {color:#64748b; font-size:0.84rem; margin-bottom:6px; font-weight:700; letter-spacing:.01em;}
    .metric-value {font-size:1.9rem; font-weight:900; color:#0f172a; line-height:1.15;}
    .metric-caption {font-size:0.86rem; color:#475569; margin-top:8px; line-height: 1.55;}
    .metric-badge {display:inline-block; margin-top:10px; background:#eff6ff; color:#1d4ed8; font-size:0.74rem; padding:5px 9px; border-radius:999px; font-weight:700;}
    .section-card {background:#ffffff; border:1px solid #e2e8f0; border-radius:20px; padding:18px 18px 14px 18px; box-shadow:0 10px 28px rgba(15,23,42,0.05); margin-bottom:16px; animation: fadeUp 0.28s ease;}
    .small-title {font-size:1.03rem; font-weight:800; color:#0f172a; margin-bottom:8px;}
    .section-subtitle {font-size:0.85rem; color:#64748b; margin-bottom:14px; line-height:1.55;}
    .alert-high,.alert-medium,.alert-low {border-radius:16px; padding:14px 16px; margin-bottom:10px; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.7);}
    .alert-high {border-left:6px solid #dc2626; background:linear-gradient(90deg, #fff5f5, #fffafb);}
    .alert-medium {border-left:6px solid #f59e0b; background:linear-gradient(90deg, #fffaf0, #fffdf7);}
    .alert-low {border-left:6px solid #059669; background:linear-gradient(90deg, #f0fdf4, #f7fffb);}
    .alert-title {font-weight:800; color:#0f172a; margin-bottom:4px;}
    .alert-detail {color:#334155; font-size:0.92rem; line-height:1.56;}
    .summary-good {border-left:6px solid #059669; background:#f0fdf4; border-radius:16px; padding:14px 16px; margin-bottom:12px;}
    .summary-bad {border-left:6px solid #dc2626; background:#fff7f7; border-radius:16px; padding:14px 16px; margin-bottom:12px;}
    .premium-note {background: linear-gradient(135deg, #eff6ff, #f8fafc); border:1px solid #dbeafe; border-radius:18px; padding:16px 18px; color:#1e3a8a;}
    .report-box textarea {font-size:0.95rem !important; line-height:1.6 !important;}
    .demo-banner {background: linear-gradient(90deg, #dbeafe, #eff6ff); border:1px solid #bfdbfe; border-radius:16px; padding:14px 18px; margin-bottom:18px; color:#1e3a8a;}
    .status-banner {background: linear-gradient(90deg, #ecfeff, #f8fafc); border:1px solid #bae6fd; border-radius:16px; padding:14px 18px; margin-bottom:18px; color:#0f172a;}
    .status-chip-row {display:flex; gap:10px; flex-wrap:wrap; margin-top:10px;}
    .status-chip {background:#ffffff; border:1px solid #dbeafe; padding:7px 10px; border-radius:999px; font-size:0.84rem; color:#0f172a;}
    [data-testid="stSidebar"] {background: linear-gradient(180deg, #0f172a 0%, #1e3a5f 100%) !important; color: #f8fafc !important;}
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stRadio,
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stExpander,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stTextInput > div > div > input {
        color: #0f172a !important;
    }
    .sidebar-card {background:rgba(255,255,255,0.14); border:1px solid rgba(191,219,254,0.22); border-radius:18px; padding:14px 14px 10px 14px; margin:10px 0 14px 0; backdrop-filter: blur(8px);}
    .sidebar-kpi {font-size:0.83rem; color:#e2e8f0; line-height:1.65;}
    .sidebar-kpi b {color:#ffffff;}
    .insight-panel {border-radius:22px; padding:20px 20px 16px 20px; margin-bottom:16px; box-shadow:0 12px 28px rgba(15,23,42,0.07);}
    .tone-navy {background:linear-gradient(135deg, #0f172a, #163a63); color:#ffffff; border:1px solid rgba(255,255,255,0.08);}
    .tone-red {background:linear-gradient(135deg, #fff7f7, #fff1f2); border:1px solid #fecaca; color:#111827;}
    .tone-amber {background:linear-gradient(135deg, #fffaf0, #fff7ed); border:1px solid #fed7aa; color:#111827;}
    .tone-green {background:linear-gradient(135deg, #ecfdf5, #f0fdf4); border:1px solid #a7f3d0; color:#111827;}
    .panel-subtitle {font-size:0.84rem; opacity:0.9; line-height:1.5; margin-bottom:10px;}
    .brief-headline {font-size:1.14rem; font-weight:800; line-height:1.55; margin-bottom:14px;}
    .insight-metrics {display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:10px; margin-bottom:12px;}
    .insight-metric {background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.14); border-radius:16px; padding:10px 12px;}
    .tone-red .insight-metric, .tone-amber .insight-metric, .tone-green .insight-metric {background:rgba(255,255,255,0.72); border-color:rgba(255,255,255,0.75);}
    .insight-metric-label {font-size:0.76rem; opacity:0.85; margin-bottom:4px;}
    .insight-metric-value {font-size:1.25rem; font-weight:900;}
    .insight-note {font-size:0.9rem; line-height:1.65; margin-bottom:8px;}
    .signal-card {border-radius:16px; padding:14px 15px; margin-bottom:10px; border:1px solid #e2e8f0; background:#ffffff; box-shadow:0 6px 18px rgba(15,23,42,0.04);}
    .signal-card.high {border-left:5px solid #dc2626;}
    .signal-card.medium {border-left:5px solid #f59e0b;}
    .signal-card.positive {border-left:5px solid #059669;}
    .signal-topline {display:flex; justify-content:space-between; gap:10px; align-items:flex-start; margin-bottom:6px;}
    .signal-title {font-size:0.94rem; font-weight:800; color:#111827;}
    .signal-impact {font-size:0.78rem; font-weight:800; color:#1e3a8a; background:#eff6ff; border-radius:999px; padding:4px 8px; white-space:nowrap;}
    .signal-detail {font-size:0.86rem; color:#475569; line-height:1.55;}
    .action-card {border-radius:16px; padding:14px 15px; margin-bottom:10px; border:1px solid #dbeafe; background:linear-gradient(135deg, #ffffff, #f8fbff);}
    .action-period {display:inline-block; font-size:0.76rem; font-weight:800; color:#1d4ed8; background:#eff6ff; border-radius:999px; padding:4px 8px; margin-bottom:8px;}
    .action-title {font-size:0.93rem; font-weight:800; color:#0f172a; margin-bottom:5px; line-height:1.45;}
    .action-purpose {font-size:0.85rem; color:#475569; line-height:1.55;}
    .decision-strip {border-radius:18px; padding:16px 18px; background:linear-gradient(135deg, #ffffff, #f8fafc); border:1px solid #e2e8f0;}
    .decision-strip ul {margin:0; padding-left:18px; color:#334155; line-height:1.7;}
    .doc-card {background:#ffffff; border:1px solid #e2e8f0; border-radius:18px; padding:18px; box-shadow:0 8px 24px rgba(15,23,42,0.04);}
    .doc-list {margin:10px 0 14px 0; padding-left:18px; color:#475569; line-height:1.7;}
    div[data-testid="stTabs"] button[role="tab"] {font-weight: 700; border-radius: 999px; padding: 10px 18px;}
    div[data-testid="stTabs"] button[aria-selected="true"] {background: linear-gradient(90deg, #dbeafe, #eff6ff); color: #1d4ed8;}
</style>
"""


def apply_chart_theme(fig, **layout_kwargs):
    base_layout = {
        "font_family": "Pretendard, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "colorway": CHART_COLORS,
        "legend_title_text": "",
    }
    base_layout.update(layout_kwargs)
    fig.update_layout(**base_layout)
    return fig


def inject_custom_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def _escape(text: str) -> str:
    return html.escape(str(text))


def metric_card(label: str, value: str, caption: str = "", badge: str = ""):
    badge_html = f'<div class="metric-badge">{_escape(badge)}</div>' if badge else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{_escape(label)}</div>
            <div class="metric-value">{_escape(value)}</div>
            <div class="metric-caption">{_escape(caption)}</div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight_panel(title: str, subtitle: str = "", body_html: str = "", tone: str = "navy"):
    tone_class = {
        "navy": "tone-navy",
        "red": "tone-red",
        "amber": "tone-amber",
        "green": "tone-green",
    }.get(tone, "tone-navy")
    subtitle_html = f'<div class="panel-subtitle">{_escape(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f'<div class="insight-panel {tone_class}"><div class="small-title">{_escape(title)}</div>{subtitle_html}{body_html}</div>',
        unsafe_allow_html=True,
    )


def render_signal_card(title: str, detail: str, impact: str = "", tone: str = "high"):
    tone_class = tone if tone in {"high", "medium", "positive"} else "medium"
    impact_html = f'<div class="signal-impact">{_escape(impact)}</div>' if impact else ""
    st.markdown(
        f"""
        <div class="signal-card {tone_class}">
            <div class="signal-topline">
                <div class="signal-title">{_escape(title)}</div>
                {impact_html}
            </div>
            <div class="signal-detail">{_escape(detail)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_action_card(period: str, action: str, purpose: str):
    st.markdown(
        f"""
        <div class="action-card">
            <div class="action-period">{_escape(period)}</div>
            <div class="action-title">{_escape(action)}</div>
            <div class="action-purpose">{_escape(purpose)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alert_card(row):
    severity_class = {"High": "alert-high", "Medium": "alert-medium", "Low": "alert-low"}.get(row["severity"], "alert-low")
    st.markdown(
        f"""
        <div class="{severity_class}">
            <div class="alert-title">[{_escape(row['severity'])}] {_escape(row['company_name'])} · {_escape(row['alert_type'])}</div>
            <div class="alert-detail">{_escape(row['detail'])}</div>
            <div class="alert-detail" style="margin-top:6px;"><b>권고 조치</b> · {_escape(row['recommended_action'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_reason_box(title: str, content: str, positive: bool = True):
    css_class = "summary-good" if positive else "summary-bad"
    st.markdown(
        f"""
        <div class="{css_class}">
            <div class="alert-title">{_escape(title)}</div>
            <div class="alert-detail">{_escape(content)}</div>
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
        color_continuous_scale="Reds",
        labels={"x": "리스크 축", "y": "계열사", "color": "점수"},
    )
    return apply_chart_theme(fig, height=340, margin=dict(l=0, r=0, t=24, b=0))


def build_segment_heatmap_figure(segment_table: pd.DataFrame):
    required_columns = ["세그먼트", "현재 연체율", "연체율 변화(%p)", "현재 잔액", "차주수 변화"]
    if segment_table is None or segment_table.empty or any(col not in segment_table.columns for col in required_columns):
        return None

    heatmap_df = segment_table[required_columns].copy().head(8).set_index("세그먼트")
    normalized = pd.DataFrame(index=heatmap_df.index)
    for source, label in [
        ("현재 연체율", "연체율 수준"),
        ("연체율 변화(%p)", "전월 변화"),
        ("현재 잔액", "잔액 규모"),
        ("차주수 변화", "차주수 변화"),
    ]:
        series = pd.to_numeric(heatmap_df[source], errors="coerce").fillna(0)
        max_abs = max(abs(series).max(), 1)
        normalized[label] = (series / max_abs * 100).round(0)

    fig = px.imshow(
        normalized,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdYlGn_r",
        color_continuous_midpoint=0,
        labels={"x": "위험 축", "y": "세그먼트", "color": "상대 강도"},
    )
    return apply_chart_theme(fig, height=380, margin=dict(l=0, r=0, t=24, b=0))
