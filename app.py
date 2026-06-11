from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

from risk_engine import (
    answer_question,
    calculate_company_risk,
    detect_alerts,
    generate_delinquency_reason_report,
    generate_executive_report,
    get_action_item_table,
    get_agent_execution_table,
    get_company_comparison,
    get_delinquency_snapshot,
    get_enterprise_portfolio_summary,
    get_segment_detail_table,
    simulate_what_if_scenario,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
METRICS_PATH = DATA_DIR / "sample_risk_metrics.csv"
LOGS_PATH = DATA_DIR / "sample_risk_logs.csv"
DRIVERS_PATH = DATA_DIR / "sample_delinquency_drivers.csv"
SEGMENT_PATH = DATA_DIR / "sample_segment_metrics.csv"

REQUIRED_COLUMNS = {
    "metrics": [
        "date",
        "company_name",
        "company_type",
        "delinquency_rate",
        "complaints",
        "abnormal_events",
        "exposure_real_estate",
        "exposure_sme",
    ],
    "logs": ["date", "company_name", "issue_type", "severity", "description"],
    "drivers": ["date", "company_name", "driver_name", "direction", "contribution_bps", "description"],
    "segments": ["date", "company_name", "segment_name", "balance", "delinquency_rate", "customer_count"],
}

DEMO_MODES = {
    "전체 흐름": "Orchestrator Agent가 전체 그룹을 스캔하고 핵심 Watchlist를 지정하는 기본 시연 모드입니다.",
    "Step 1. 그룹 스캔": "그룹 기준 최고 위험 계열사, 경보 건수, 비교 랭킹을 먼저 보여주는 심사위원용 시작 장면입니다.",
    "Step 2. PF/기업대출 분석": "PF Surveillance Agent와 Corporate Loan Agent가 세그먼트 악화 원인을 drill-down 하는 장면입니다.",
    "Step 3. 담보/회수 우선순위": "Collateral & Recovery Agent가 담보 재평가와 회수정책 우선순위를 제시하는 장면입니다.",
    "Step 4. 경영진 보고": "Executive Reporting Agent가 보고서와 질의응답으로 마무리하는 장면입니다.",
}

FOCUS_MODE_TO_DEMO = {
    "그룹 스캔": "Step 1. 그룹 스캔",
    "PF 집중 점검": "Step 2. PF/기업대출 분석",
    "기업대출 점검": "Step 2. PF/기업대출 분석",
    "담보·회수 점검": "Step 3. 담보/회수 우선순위",
    "경영진 보고": "Step 4. 경영진 보고",
}

st.set_page_config(page_title="JB Insight CRO Multi-Agent", page_icon="🤖", layout="wide")

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

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data
def load_data():
    metrics = pd.read_csv(METRICS_PATH, parse_dates=["date"])
    logs = pd.read_csv(LOGS_PATH, parse_dates=["date"])
    drivers = pd.read_csv(DRIVERS_PATH, parse_dates=["date"])
    segments = pd.read_csv(SEGMENT_PATH, parse_dates=["date"])
    return metrics, logs, drivers, segments


def validate_required_columns(name: str, df: pd.DataFrame, required_columns: list[str]):
    return [col for col in required_columns if col not in df.columns]


@st.cache_data
def build_dashboard_data(metrics_df: pd.DataFrame, logs_df: pd.DataFrame, drivers_df: pd.DataFrame, segment_df: pd.DataFrame):
    risk = calculate_company_risk(metrics_df, logs_df, drivers_df)
    alerts = detect_alerts(metrics_df, logs_df)
    comparison = get_company_comparison(risk)
    return risk, alerts, comparison


def stop_with_deploy_diagnostics(message: str, diagnostics=None):
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.error(message)
    if diagnostics:
        with st.expander("배포 진단 정보", expanded=True):
            st.json(diagnostics)
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


def ensure_dataframe_columns(df, defaults: dict):
    base = df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    for column, default in defaults.items():
        if column not in base.columns:
            base[column] = default
    return base


def fallback_snapshot(company_name: str):
    return {
        "current_rate": 0.0,
        "previous_rate": 0.0,
        "mom_change_pp": 0.0,
        "mom_change_pct": 0.0,
        "trailing_3m_avg": 0.0,
        "vs_3m_avg_pp": 0.0,
        "headline": f"{company_name} 기준 데이터가 충분하지 않아 기본값으로 표시 중입니다.",
        "positive_driver_summary": "개선 요인 데이터 없음",
        "negative_driver_summary": "악화 요인 데이터 없음",
    }


def fallback_portfolio_summary():
    return {
        "pf_share": 0.0,
        "secured_share": 0.0,
        "worst_segment": "데이터 없음",
        "worst_change_pp": 0.0,
        "best_segment": "데이터 없음",
        "best_change_pp": 0.0,
        "largest_balance_segment": "데이터 없음",
        "largest_balance": 0.0,
    }


def fallback_comparison_data():
    return {
        "best_company": "N/A",
        "best_change_pp": 0.0,
        "best_summary": "비교 데이터 없음",
        "worst_company": "N/A",
        "worst_change_pp": 0.0,
        "worst_summary": "비교 데이터 없음",
        "trend_table": pd.DataFrame(columns=["계열사", "전월 대비 변화(%p)", "3개월 평균 대비(%p)", "현재 연체율"]),
    }


def safe_generate_reason_report(metrics_df, drivers_df, segment_df, company_name: str):
    try:
        return generate_delinquency_reason_report(metrics_df, drivers_df, segment_df, company_name)
    except Exception as exc:
        return f"[안정화 모드] Driver Analysis Agent 보고서 생성 중 예외가 발생했습니다: {exc}"


def safe_generate_executive_report(risk_df, alerts_df, latest_month: str):
    try:
        return generate_executive_report(risk_df, alerts_df, latest_month)
    except Exception as exc:
        return f"[안정화 모드] Orchestrator Agent 그룹 브리프 생성 중 예외가 발생했습니다: {exc}"


def safe_answer_question(question: str, risk_df, alerts_df, metrics_df):
    try:
        return answer_question(question, risk_df, alerts_df, metrics_df)
    except Exception as exc:
        return f"[안정화 모드] Interactive Q&A Agent 응답 생성 중 예외가 발생했습니다: {exc}"


def safe_simulate_what_if(selected_company: str, risk_df, segment_df, pf_stress: float, collateral_stress: float, sme_stress: float):
    try:
        return simulate_what_if_scenario(
            selected_company,
            risk_df,
            segment_df,
            pf_refinancing_shock_pp=pf_stress,
            collateral_recovery_drop_pp=collateral_stress,
            sme_slowdown_shock_pp=sme_stress,
        )
    except Exception as exc:
        base_rate = 0.0
        if isinstance(risk_df, pd.DataFrame) and not risk_df.empty and "company_name" in risk_df.columns and "latest_delinquency_rate" in risk_df.columns:
            matched = risk_df[risk_df["company_name"] == selected_company]
            if not matched.empty:
                base_rate = float(matched.iloc[0]["latest_delinquency_rate"])
        stress_delta = round(float(pf_stress) + float(collateral_stress) + float(sme_stress), 2)
        return {
            "base_rate": base_rate,
            "projected_rate": round(base_rate + stress_delta, 2),
            "stress_delta": stress_delta,
            "projected_risk_score": 0,
            "projected_risk_level": "Unknown",
            "impact_summary": f"안정화 모드 fallback 적용 · {exc}",
        }


def render_deploy_status_banner(metrics_df, risk_df, alerts_df, latest_month: str):
    metrics_rows = len(metrics_df) if isinstance(metrics_df, pd.DataFrame) else 0
    risk_rows = len(risk_df) if isinstance(risk_df, pd.DataFrame) else 0
    alerts_rows = len(alerts_df) if isinstance(alerts_df, pd.DataFrame) else 0
    expected_python = "3.11"
    runtime_python = f"{sys.version_info.major}.{sys.version_info.minor}"
    driver = "정상" if metrics_rows > 0 and risk_rows > 0 else "점검 필요"
    banner = f"""
    <div class="status-banner">
        <b>배포 상태 배너</b><br>
        현재 화면은 배포 진단 정보를 함께 노출합니다. 데이터 적재, 리스크 계산, 핵심 테이블 생성 여부를 첫 화면에서 바로 확인할 수 있습니다.
        <div class="status-chip-row">
            <div class="status-chip">기준 월 · {latest_month}</div>
            <div class="status-chip">metrics rows · {metrics_rows}</div>
            <div class="status-chip">risk rows · {risk_rows}</div>
            <div class="status-chip">alerts rows · {alerts_rows}</div>
            <div class="status-chip">expected python · {expected_python}</div>
            <div class="status-chip">runtime python · {runtime_python}</div>
            <div class="status-chip">healthcheck · {driver}</div>
        </div>
    </div>
    """
    st.markdown(banner, unsafe_allow_html=True)


def render_healthcheck_expander(metrics_df, logs_df, drivers_df, segment_df, risk_df, alerts_df):
    st.markdown("#### 헬스체크 · 배포 진단 요약")
    health_df = pd.DataFrame(
        [
            {"항목": "metrics_df", "rows": len(metrics_df), "columns": len(metrics_df.columns)},
            {"항목": "logs_df", "rows": len(logs_df), "columns": len(logs_df.columns)},
            {"항목": "drivers_df", "rows": len(drivers_df), "columns": len(drivers_df.columns)},
            {"항목": "segment_df", "rows": len(segment_df), "columns": len(segment_df.columns)},
            {"항목": "risk_df", "rows": len(risk_df), "columns": len(risk_df.columns)},
            {"항목": "alerts_df", "rows": len(alerts_df), "columns": len(alerts_df.columns)},
        ]
    )
    st.dataframe(health_df, use_container_width=True, hide_index=True)
    st.caption("클라우드 배포 시 Python 3.11 고정을 권장합니다.")


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


startup_diagnostics = {"base_dir": str(BASE_DIR), "data_dir": str(DATA_DIR)}

try:
    metrics_df, logs_df, drivers_df, segment_df = load_data()
except Exception as exc:
    stop_with_deploy_diagnostics("데이터 파일 로드 단계에서 예외가 발생했습니다.", startup_diagnostics | {"error": repr(exc)})

missing_columns = {}
for key, df in {
    "metrics": metrics_df,
    "logs": logs_df,
    "drivers": drivers_df,
    "segments": segment_df,
}.items():
    startup_diagnostics[key] = {"rows": int(len(df)), "columns": list(df.columns)}
    missing = validate_required_columns(key, df, REQUIRED_COLUMNS[key])
    if missing:
        missing_columns[key] = missing

if missing_columns:
    stop_with_deploy_diagnostics("배포 데이터 스키마 불일치가 감지되었습니다.", startup_diagnostics | {"missing_columns": missing_columns})

try:
    risk_df, alerts_df, comparison_data = build_dashboard_data(metrics_df, logs_df, drivers_df, segment_df)
except Exception as exc:
    stop_with_deploy_diagnostics("리스크 계산 단계에서 예외가 발생했습니다.", startup_diagnostics | {"error": repr(exc)})

if metrics_df.empty:
    stop_with_deploy_diagnostics("sample_risk_metrics.csv가 비어 있어 화면을 구성할 수 없습니다.", startup_diagnostics)

risk_df = ensure_dataframe_columns(
    risk_df,
    {
        "company_name": "",
        "company_type": "Unknown",
        "risk_score": 0.0,
        "risk_level": "Low",
        "latest_delinquency_rate": 0.0,
        "delinquency_change_pp": 0.0,
        "vs_3m_avg_pp": 0.0,
        "positive_driver_summary": "개선 요인 데이터 없음",
        "negative_driver_summary": "악화 요인 데이터 없음",
        "top_drivers": "데이터 없음",
        "executive_headline": "데이터 없음",
    },
)
alerts_df = ensure_dataframe_columns(
    alerts_df,
    {
        "severity": "Low",
        "company_name": "",
        "alert_type": "N/A",
        "detail": "상세 정보 없음",
        "recommended_action": "기본 모니터링 유지",
    },
)

latest_date = metrics_df["date"].dropna().max() if "date" in metrics_df.columns else pd.NaT
latest_month = latest_date.strftime("%Y-%m") if pd.notna(latest_date) else "N/A"
company_options = sorted([str(name) for name in metrics_df["company_name"].dropna().tolist() if str(name).strip()])
company_options = sorted(list(dict.fromkeys(company_options)))
if not company_options:
    stop_with_deploy_diagnostics("company_name 값이 비어 있어 메인 스토리 계열사를 선택할 수 없습니다.", startup_diagnostics)

preferred_company = "JB우리캐피탈" if "JB우리캐피탈" in company_options else company_options[0]
if "selected_company" not in st.session_state or st.session_state.get("selected_company") not in company_options:
    st.session_state["selected_company"] = preferred_company
if "demo_mode" not in st.session_state:
    st.session_state["demo_mode"] = "전체 흐름"
if "focus_mode" not in st.session_state:
    st.session_state["focus_mode"] = "그룹 스캔"

with st.sidebar:
    st.header("리스크 관제 설정")
    st.caption("실무 관제 화면 기준으로 필터와 점검 조건만 남겼습니다.")

    selected_company = st.selectbox(
        "주요 점검 계열사",
        company_options,
        key="selected_company",
    )

    focus_mode = st.radio(
        "관제 초점",
        ["그룹 스캔", "PF 집중 점검", "기업대출 점검", "담보·회수 점검", "경영진 보고"],
        key="focus_mode",
    )
    st.session_state["demo_mode"] = FOCUS_MODE_TO_DEMO.get(focus_mode, "전체 흐름")

    severity_filter = st.multiselect(
        "경보 등급",
        ["High", "Medium", "Low"],
        default=["High", "Medium"],
        help="실무 화면에서는 High·Medium 중심으로 먼저 보는 흐름이 더 자연스럽습니다.",
    )

    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.markdown("**현재 관제 기준**")
    st.markdown(
        f'<div class="sidebar-kpi"><b>기준 월</b> · {latest_month}<br><b>메인 포트폴리오</b> · {selected_company}<br><b>관제 초점</b> · {focus_mode}<br><b>경보 필터</b> · {", ".join(severity_filter) if severity_filter else "없음"}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("질의응답 · 보고서 도구", expanded=False):
        demo_question = st.selectbox(
            "질문 선택",
            [
                "Orchestrator가 지정한 최우선 리스크는?",
                "PF Surveillance Agent가 본 핵심 세그먼트는?",
                "Collateral & Recovery Agent가 우선 점검할 항목은?",
                "Benchmark Agent가 비교한 개선 벤치마크는?",
            ],
        )
        if st.button("Q&A 실행", use_container_width=True):
            st.session_state["qa_answer"] = safe_answer_question(demo_question, risk_df, alerts_df, metrics_df)
        if st.button("원인 분석 보고서 갱신", use_container_width=True):
            st.session_state["reason_report"] = safe_generate_reason_report(metrics_df, drivers_df, segment_df, selected_company)
            st.session_state["reason_report_company"] = selected_company

    st.caption("사이드바는 점검 조건 중심으로 최소화했습니다.")

selected_snapshot = fallback_snapshot(selected_company)
try:
    selected_snapshot.update(get_delinquency_snapshot(risk_df, selected_company) or {})
except Exception:
    pass

selected_risk_candidates = risk_df[risk_df["company_name"] == selected_company]
if not selected_risk_candidates.empty:
    selected_risk_row = selected_risk_candidates.iloc[0]
else:
    selected_risk_row = pd.Series({
        "company_name": selected_company,
        "top_drivers": "데이터 없음",
        "negative_driver_summary": "악화 요인 데이터 없음",
        "positive_driver_summary": "개선 요인 데이터 없음",
    })

try:
    segment_table = get_segment_detail_table(segment_df, selected_company)
except Exception:
    segment_table = pd.DataFrame()
segment_table = ensure_dataframe_columns(
    segment_table,
    {
        "세그먼트": "데이터 없음",
        "연체율 변화(%p)": 0.0,
        "담보유형": "미분류",
        "잔액 변화": 0.0,
        "현재 잔액": 0.0,
        "업종": "미분류",
    },
)

portfolio_summary = fallback_portfolio_summary()
try:
    portfolio_summary.update(get_enterprise_portfolio_summary(segment_df, selected_company) or {})
except Exception:
    pass

comparison_defaults = fallback_comparison_data()
comparison_data = comparison_data if isinstance(comparison_data, dict) else {}
for key, value in comparison_defaults.items():
    comparison_data.setdefault(key, value)
comparison_data["trend_table"] = ensure_dataframe_columns(
    comparison_data.get("trend_table"),
    {"계열사": "", "전월 대비 변화(%p)": 0.0, "3개월 평균 대비(%p)": 0.0, "현재 연체율": 0.0},
)

filtered_alerts = alerts_df[alerts_df["severity"].isin(severity_filter)].copy() if "severity" in alerts_df.columns else pd.DataFrame()
max_score_company = risk_df.sort_values("risk_score", ascending=False).iloc[0] if not risk_df.empty else pd.Series({"company_name": selected_company, "risk_score": 0.0})
high_alert_count = int((alerts_df["severity"] == "High").sum()) if "severity" in alerts_df.columns else 0
avg_score = round(pd.to_numeric(risk_df["risk_score"], errors="coerce").dropna().mean(), 1) if not risk_df.empty else 0.0

try:
    agent_trace_df = get_agent_execution_table(selected_company, risk_df, alerts_df, segment_df)
except Exception as exc:
    agent_trace_df = pd.DataFrame([
        {"Agent": "Orchestrator Agent", "입력": "배포 데이터", "핵심 판단": "안정화 fallback 적용", "출력": str(exc)}
    ])
agent_trace_df = ensure_dataframe_columns(agent_trace_df, {"Agent": "Orchestrator Agent", "입력": "-", "핵심 판단": "-", "출력": "-"})

try:
    action_item_df = get_action_item_table(selected_company, risk_df, alerts_df, segment_df)
except Exception as exc:
    action_item_df = pd.DataFrame([
        {"시점": "오늘", "담당 Agent": "Orchestrator Agent", "액션 아이템": "배포 오류 원인 확인", "기대 효과": str(exc)}
    ])
action_item_df = ensure_dataframe_columns(action_item_df, {"시점": "오늘", "담당 Agent": "Orchestrator Agent", "액션 아이템": "데이터 확인", "기대 효과": "기본 안정화"})

st.markdown(
    f"""
    <div class="hero-wrap">
        <div class="hero-kicker">JB WOORI CAPITAL · CORPORATE FINANCE RISK DASHBOARD</div>
        <div class="hero-title">JB우리캐피탈 기업금융 리스크 관제 대시보드</div>
        <div class="hero-subtitle">
            JB우리캐피탈 기업금융 포트폴리오를 기준으로 PF 브릿지론·본PF 참여금융·중소법인 담보대출·설비금융·건설협력업체 운전자금을
            월간 건전성 관점에서 재구성했습니다. 상단은 경영진 KPI, 중단은 조기경보와 계열 비교, 하단은 포트폴리오 세부 진단과 대응계획으로
            나누어 실제 기업금융 리스크관리 회의 자료처럼 읽히도록 재설계했습니다.
        </div>
        <div class="info-chip-row">
            <div class="info-chip">기준 월 · {latest_month}</div>
            <div class="info-chip">주요 점검 계열사 · {selected_company}</div>
            <div class="info-chip">당월 최우선 점검 계열사 · {max_score_company['company_name']}</div>
            <div class="info-chip">High 경보 건수 · {high_alert_count}건</div>
            <div class="info-chip">PF/프로젝트금융 비중 · {portfolio_summary['pf_share']}%</div>
            <div class="info-chip">담보 기반 익스포저 비중 · {portfolio_summary['secured_share']}%</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("배포 상태 / 헬스체크", expanded=False):
    render_deploy_status_banner(metrics_df, risk_df, alerts_df, latest_month)
    render_healthcheck_expander(metrics_df, logs_df, drivers_df, segment_df, risk_df, alerts_df)

st.markdown(
    f"""
    <div class="demo-banner">
        <b>현재 점검 시나리오 · {st.session_state['demo_mode']}</b><br>
        {DEMO_MODES.get(st.session_state['demo_mode'], DEMO_MODES['전체 흐름'])}
    </div>
    """,
    unsafe_allow_html=True,
)

row1 = st.columns(4)
with row1[0]:
    metric_card("당월 최우선 점검 계열사", max_score_company["company_name"], "그룹 차원에서 우선 점검이 필요한 계열사", "Watchlist")
with row1[1]:
    metric_card("그룹 평균 위험도", f"{avg_score}점", "계열사 평균 리스크 점수", "Group Risk")
with row1[2]:
    metric_card(f"{selected_company} 기업금융 연체율", f"{selected_snapshot['current_rate']:.2f}%", selected_snapshot["headline"], "Core KPI")
with row1[3]:
    metric_card("당월 조기경보", f"{len(alerts_df)}건", f"High {high_alert_count}건 포함", "Early Warning")

row2 = st.columns(4)
with row2[0]:
    metric_card("전월 대비 연체율 변화", f"{selected_snapshot['mom_change_pp']:+.2f}%p", f"변화율 {selected_snapshot['mom_change_pct']}%", "MoM")
with row2[1]:
    metric_card("3개월 평균 대비 이탈", f"{selected_snapshot['vs_3m_avg_pp']:+.2f}%p", f"3개월 평균 {selected_snapshot['trailing_3m_avg']:.2f}%", "Trend")
with row2[2]:
    metric_card("건전성 개선 우수사례", comparison_data["best_company"], f"{comparison_data['best_change_pp']:+.2f}%p · {comparison_data['best_summary']}", "Best Practice")
with row2[3]:
    metric_card("집중 관리 필요 계열사", comparison_data["worst_company"], f"{comparison_data['worst_change_pp']:+.2f}%p · {comparison_data['worst_summary']}", "Attention")

st.markdown("### 경영관리 화면")
tab1, tab2, tab3, tab4 = st.tabs([
    "1. 경영진 요약",
    "2. 조기경보 · 계열 비교",
    "3. 포트폴리오 세부진단",
    "4. 대응계획 · 보고서 · Q&A",
])

with tab1:
    top_a, top_b, top_c = st.columns(3)
    with top_a:
        metric_card("메인 리스크 세그먼트", portfolio_summary["worst_segment"], f"연체율 변화 {portfolio_summary['worst_change_pp']:+.2f}%p", "Priority 1")
    with top_b:
        metric_card("개선 확인 세그먼트", portfolio_summary["best_segment"], f"연체율 변화 {portfolio_summary['best_change_pp']:+.2f}%p", "Positive Signal")
    with top_c:
        metric_card("최대 익스포저 세그먼트", portfolio_summary["largest_balance_segment"], f"현재 잔액 {portfolio_summary['largest_balance']}", "Exposure")

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="small-title">{selected_company} 경영진 핵심 메시지</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">그룹 관제 결과를 문제 징후 → 원인 → 대응 시사점 구조로 정리했습니다.</div>', unsafe_allow_html=True)
    st.markdown(f"- 문제 징후: {selected_company}의 전사 연체율은 전월 대비 **{selected_snapshot['mom_change_pp']:+.2f}%p**, 3개월 평균 대비 **{selected_snapshot['vs_3m_avg_pp']:+.2f}%p** 변동했습니다.")
    st.markdown(f"- 핵심 원인: **{selected_snapshot['negative_driver_summary']}**")
    st.markdown(f"- 대응 시사점: **{portfolio_summary['worst_segment']}** 중심으로 차환 일정, 담보 재평가, 회수 우선순위를 재점검해야 합니다.")
    st.markdown('</div>', unsafe_allow_html=True)

    left, right = st.columns([1.05, 0.95])
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">분석 워크플로우</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">각 분석 모듈의 입력, 판단, 산출물을 한 줄로 정리했습니다.</div>', unsafe_allow_html=True)
        st.dataframe(agent_trace_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">대응 일정 및 담당</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">오늘 · 이번 주 · 다음 달 단위로 실행 항목을 정리했습니다.</div>', unsafe_allow_html=True)
        st.dataframe(action_item_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    left, right = st.columns([1.1, 0.9])
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">계열사 건전성 비교</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">전월 대비 변화와 최근 추세 이탈을 함께 비교합니다.</div>', unsafe_allow_html=True)
        ranked = risk_df[["company_name", "company_type", "risk_score", "risk_level", "latest_delinquency_rate", "delinquency_change_pp", "vs_3m_avg_pp", "positive_driver_summary", "negative_driver_summary"]].rename(
            columns={
                "company_name": "계열사",
                "company_type": "유형",
                "risk_score": "리스크 점수",
                "risk_level": "위험 단계",
                "latest_delinquency_rate": "현재 연체율",
                "delinquency_change_pp": "전월 대비 변화(%p)",
                "vs_3m_avg_pp": "3개월 평균 대비(%p)",
                "positive_driver_summary": "개선 요인",
                "negative_driver_summary": "악화 요인",
            }
        )
        st.dataframe(ranked, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">그룹 위험도 분포</div>', unsafe_allow_html=True)
        if risk_df.empty:
            st.info("표시할 리스크 점수 데이터가 없습니다.")
        else:
            fig = px.bar(
                risk_df.sort_values("risk_score", ascending=True),
                x="risk_score",
                y="company_name",
                color="risk_level",
                text="risk_score",
                orientation="h",
                color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"},
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">조기경보 상세</div>', unsafe_allow_html=True)
        if filtered_alerts.empty:
            st.info("표시할 경보가 없습니다.")
        else:
            for _, row in filtered_alerts.head(8).iterrows():
                render_alert_card(row)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">그룹 핵심지표 추이</div>', unsafe_allow_html=True)
        metric_choice = st.selectbox("추이 지표 선택", ["delinquency_rate", "complaints", "abnormal_events", "exposure_real_estate", "exposure_sme"], index=0)
        metric_label_map = {
            "delinquency_rate": "연체율",
            "complaints": "민원 건수",
            "abnormal_events": "이상 이벤트 수",
            "exposure_real_estate": "부동산 익스포저",
            "exposure_sme": "중소기업 익스포저",
        }
        if metrics_df.empty or metric_choice not in metrics_df.columns:
            st.info("추이 차트를 그릴 데이터가 없습니다.")
        else:
            trend_fig = px.line(
                metrics_df.sort_values("date"),
                x="date",
                y=metric_choice,
                color="company_name",
                markers=True,
                title=f"월별 {metric_label_map[metric_choice]} 추이",
            )
            trend_fig.update_layout(height=410, margin=dict(l=0, r=0, t=44, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(trend_fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="small-title">개선 · 악화 비교표</div>', unsafe_allow_html=True)
    st.dataframe(comparison_data["trend_table"], use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    top_left, top_right = st.columns([0.95, 1.05])
    with top_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="small-title">{selected_company} 연체율 변동 원인 요약</div>', unsafe_allow_html=True)
        render_reason_box("경영진 해석", selected_snapshot["headline"], positive=(selected_snapshot["mom_change_pp"] <= 0))
        render_reason_box("연체율 하락/개선 이유", selected_snapshot["positive_driver_summary"], positive=True)
        render_reason_box("연체율 상승/악화 이유", selected_snapshot["negative_driver_summary"], positive=False)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="small-title">{selected_company} 포트폴리오 구조 요약</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="premium-note">PF 비중 <b>{portfolio_summary["pf_share"]}%</b> · 담보 기반 비중 <b>{portfolio_summary["secured_share"]}%</b><br>'
            f'가장 큰 세그먼트는 <b>{portfolio_summary["largest_balance_segment"]}</b>이며 잔액은 <b>{portfolio_summary["largest_balance"]}</b>입니다.<br>'
            f'가장 악화된 세그먼트는 <b>{portfolio_summary["worst_segment"]}</b>({portfolio_summary["worst_change_pp"]:+.2f}%p), '
            f'가장 개선된 세그먼트는 <b>{portfolio_summary["best_segment"]}</b>({portfolio_summary["best_change_pp"]:+.2f}%p)입니다.</div>',
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        snapshot_cols = st.columns(4)
        with snapshot_cols[0]:
            metric_card("PF/프로젝트금융 비중", f"{portfolio_summary['pf_share']:.1f}%", "기업금융 내 PF 익스포저 비중", "Portfolio")
        with snapshot_cols[1]:
            metric_card("담보 기반 익스포저 비중", f"{portfolio_summary['secured_share']:.1f}%", "부동산·설비 등 담보 기반 포트폴리오 비중", "Collateral")
        with snapshot_cols[2]:
            metric_card("최대 익스포저 세그먼트", portfolio_summary['largest_balance_segment'], f"현재 잔액 {portfolio_summary['largest_balance']:.1f}", "Exposure")
        with snapshot_cols[3]:
            metric_card("집중 관리 세그먼트", portfolio_summary['worst_segment'], f"연체율 변화 {portfolio_summary['worst_change_pp']:+.2f}%p", "Priority")
    with top_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="small-title">{selected_company} 세그먼트 상세 변화</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">PF, 담보대출, 운전자금 세그먼트를 한 화면에서 비교합니다.</div>', unsafe_allow_html=True)
        st.dataframe(segment_table, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    mid_left, mid_right = st.columns([1, 1])
    with mid_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">세그먼트별 연체율 변화</div>', unsafe_allow_html=True)
        if segment_table.empty:
            st.info("세그먼트 변화 데이터가 없습니다.")
        else:
            seg_fig = px.bar(
                segment_table,
                x="세그먼트",
                y="연체율 변화(%p)",
                color="담보유형",
                text="연체율 변화(%p)",
                title="세그먼트 연체율 변화",
            )
            seg_fig.update_layout(height=380, margin=dict(l=0, r=0, t=44, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(seg_fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with mid_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">담보 · 회수 관점 포지셔닝</div>', unsafe_allow_html=True)
        if segment_table.empty:
            st.info("리스크 포지셔닝 산포도에 사용할 데이터가 없습니다.")
        else:
            scatter = px.scatter(
                segment_table,
                x="잔액 변화",
                y="연체율 변화(%p)",
                size="현재 잔액",
                color="담보유형",
                hover_name="세그먼트",
                symbol="업종",
                title="잔액 증가와 연체율 변화를 동시 점검",
            )
            scatter.update_layout(height=380, margin=dict(l=0, r=0, t=44, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(scatter, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="small-title">스트레스 시나리오 점검</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">PF 차환 부담, 담보 회수율 저하, SME 업황 악화가 동시에 발생할 때의 영향을 계산합니다.</div>', unsafe_allow_html=True)
    slider_col1, slider_col2, slider_col3 = st.columns(3)
    with slider_col1:
        pf_stress = st.slider("PF 차환 부담 가정(%p)", min_value=0.0, max_value=1.2, value=0.3, step=0.05)
    with slider_col2:
        collateral_stress = st.slider("담보 회수율 저하 가정(%p)", min_value=0.0, max_value=1.0, value=0.2, step=0.05)
    with slider_col3:
        sme_stress = st.slider("SME 업황 악화 가정(%p)", min_value=0.0, max_value=1.0, value=0.15, step=0.05)

    scenario_result = safe_simulate_what_if(
        selected_company,
        risk_df,
        segment_df,
        pf_stress,
        collateral_stress,
        sme_stress,
    )

    scenario_metrics = st.columns(4)
    with scenario_metrics[0]:
        metric_card("현재 연체율", f"{scenario_result['base_rate']:.2f}%", "기준 시점", "Baseline")
    with scenario_metrics[1]:
        metric_card("Projected 연체율", f"{scenario_result['projected_rate']:.2f}%", "스트레스 반영 후", "Scenario")
    with scenario_metrics[2]:
        metric_card("추가 충격", f"{scenario_result['stress_delta']:+.2f}%p", scenario_result["impact_summary"], "Shock")
    with scenario_metrics[3]:
        metric_card("Projected 위험 단계", scenario_result["projected_risk_level"], f"예상 리스크 점수 {scenario_result['projected_risk_score']}", "Risk Level")

    scenario_df = pd.DataFrame(
        {
            "구분": ["기준 연체율", "Projected 연체율"],
            "연체율": [scenario_result["base_rate"], scenario_result["projected_rate"]],
        }
    )
    scenario_fig = px.bar(scenario_df, x="구분", y="연체율", color="구분", text="연체율", title="What-if 결과 비교")
    scenario_fig.update_layout(height=320, margin=dict(l=0, r=0, t=44, b=0), showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(scenario_fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    left, right = st.columns([1.05, 0.95])
    with left:
        st.markdown('<div class="section-card report-box">', unsafe_allow_html=True)
        st.markdown(f'<div class="small-title">{selected_company} 임원 보고용 연체율 분석</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">각 분석 결과를 임원 보고 문장으로 통합합니다.</div>', unsafe_allow_html=True)
        if "reason_report" not in st.session_state or st.session_state.get("reason_report_company") != selected_company:
            st.session_state["reason_report"] = safe_generate_reason_report(metrics_df, drivers_df, segment_df, selected_company)
            st.session_state["reason_report_company"] = selected_company
        if st.button("임원 보고서 새로고침", use_container_width=True):
            st.session_state["reason_report"] = safe_generate_reason_report(metrics_df, drivers_df, segment_df, selected_company)
            st.session_state["reason_report_company"] = selected_company
        st.text_area("임원 보고서 출력", st.session_state["reason_report"], height=460)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card report-box">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">그룹 리스크 브리프</div>', unsafe_allow_html=True)
        if st.button("그룹 브리프 생성", use_container_width=True):
            st.session_state["executive_report"] = safe_generate_executive_report(risk_df, alerts_df, latest_month)
        if "executive_report" not in st.session_state:
            st.session_state["executive_report"] = safe_generate_executive_report(risk_df, alerts_df, latest_month)
        st.text_area("그룹 브리프 출력", st.session_state["executive_report"], height=300)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">경영진 Q&A</div>', unsafe_allow_html=True)
        if "qa_answer" in st.session_state:
            st.success(st.session_state["qa_answer"])
        else:
            st.caption("좌측 사이드바에서 질문을 선택해 실행하세요.")
        st.markdown("#### 현재 선택 계열사 핵심 요인")
        driver_items = [item.strip() for item in str(selected_risk_row.get("top_drivers", "")).split("|") if item.strip()]
        if driver_items:
            for item in driver_items:
                st.markdown(f"- {item}")
        else:
            st.caption("표시할 핵심 요인이 없습니다.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">핵심 점검 포인트</div>', unsafe_allow_html=True)
        st.markdown("- PF 포트폴리오는 만기 구조와 차환 부담을 별도 관리")
        st.markdown("- 기업대출은 업종 편중과 차주군 질 변화를 동시 점검")
        st.markdown("- 담보/회수는 담보가치 재평가와 회수정책 실효성을 함께 추적")
        st.markdown("- 보고서는 오늘/이번 주/다음 달 액션 아이템까지 함께 제시")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">단기 실행 우선순위</div>', unsafe_allow_html=True)
        st.dataframe(action_item_df.head(5), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

st.caption("실무형 탭명, KPI 문구, JB우리캐피탈 기업금융 포트폴리오 반영 데이터, 화면 가독성 개선 반영")
