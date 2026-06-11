from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from risk_engine import (
    answer_question,
    calculate_company_risk,
    detect_alerts,
    generate_executive_report,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
METRICS_PATH = DATA_DIR / "sample_risk_metrics.csv"
LOGS_PATH = DATA_DIR / "sample_risk_logs.csv"

st.set_page_config(page_title="JB Insight CRO", page_icon="📊", layout="wide")

CUSTOM_CSS = """
<style>
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
        max-width: 1380px;
    }
    .hero-wrap {
        background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 55%, #38bdf8 100%);
        border-radius: 22px;
        padding: 28px 30px;
        color: white;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.18);
        margin-bottom: 18px;
    }
    .hero-title {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        font-size: 1rem;
        opacity: 0.92;
        line-height: 1.6;
    }
    .info-chip-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 16px;
    }
    .info-chip {
        background: rgba(255, 255, 255, 0.16);
        border: 1px solid rgba(255, 255, 255, 0.22);
        padding: 8px 12px;
        border-radius: 999px;
        font-size: 0.9rem;
    }
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    }
    .metric-label {
        color: #64748b;
        font-size: 0.9rem;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #0f172a;
    }
    .metric-caption {
        font-size: 0.85rem;
        color: #475569;
        margin-top: 6px;
    }
    .section-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 18px 18px 10px 18px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        margin-bottom: 16px;
    }
    .small-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 10px;
    }
    .alert-high {
        border-left: 6px solid #ef4444;
        background: #fff7f7;
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    .alert-medium {
        border-left: 6px solid #f59e0b;
        background: #fffbeb;
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    .alert-low {
        border-left: 6px solid #10b981;
        background: #f0fdf4;
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 10px;
    }
    .alert-title {
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }
    .alert-detail {
        color: #334155;
        font-size: 0.93rem;
        line-height: 1.5;
    }
    .driver-pill-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 6px;
    }
    .driver-pill {
        background: #eff6ff;
        color: #1d4ed8;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 0.8rem;
        border: 1px solid #bfdbfe;
    }
    .report-box textarea {
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data
def load_data():
    metrics = pd.read_csv(METRICS_PATH, parse_dates=["date"])
    logs = pd.read_csv(LOGS_PATH, parse_dates=["date"])
    return metrics, logs


@st.cache_data
def build_dashboard_data():
    metrics, logs = load_data()
    risk = calculate_company_risk(metrics, logs)
    alerts = detect_alerts(metrics, logs)
    return metrics, logs, risk, alerts


def metric_card(label: str, value: str, caption: str = ""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alert_card(row):
    severity_class = {
        "High": "alert-high",
        "Medium": "alert-medium",
        "Low": "alert-low",
    }.get(row["severity"], "alert-low")
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


metrics_df, logs_df, risk_df, alerts_df = build_dashboard_data()
latest_date = metrics_df["date"].max()
latest_month = latest_date.strftime("%Y-%m")

with st.sidebar:
    st.header("대시보드 설정")
    company_options = ["전체"] + sorted(metrics_df["company_name"].unique().tolist())
    selected_company = st.selectbox("계열사 선택", company_options)
    severity_filter = st.multiselect(
        "경보 심각도",
        options=["High", "Medium", "Low"],
        default=["High", "Medium", "Low"],
    )
    st.markdown("---")
    st.subheader("데모 질문")
    demo_question = st.selectbox(
        "질문 선택",
        [
            "이번 달 가장 위험한 계열사는?",
            "지난달 대비 가장 크게 악화된 지표는?",
            "우선 대응이 필요한 리스크는?",
            "운영리스크가 가장 큰 계열사는?",
        ],
    )
    if st.button("질문 실행", use_container_width=True):
        st.session_state["qa_answer"] = answer_question(
            demo_question, risk_df, alerts_df, metrics_df
        )
    st.markdown("---")
    st.caption("샘플 데이터 기반 MVP · 발표용 데모 버전")

filtered_metrics = metrics_df.copy()
filtered_risk = risk_df.copy()
filtered_alerts = alerts_df.copy()
filtered_logs = logs_df.copy()

if selected_company != "전체":
    filtered_metrics = filtered_metrics[filtered_metrics["company_name"] == selected_company]
    filtered_risk = filtered_risk[filtered_risk["company_name"] == selected_company]
    filtered_alerts = filtered_alerts[filtered_alerts["company_name"] == selected_company]
    filtered_logs = filtered_logs[filtered_logs["company_name"] == selected_company]

filtered_alerts = filtered_alerts[filtered_alerts["severity"].isin(severity_filter)]

max_score_company = risk_df.sort_values("risk_score", ascending=False).iloc[0]
high_alert_count = len(alerts_df[alerts_df["severity"] == "High"])
avg_score = round(risk_df["risk_score"].mean(), 1)

st.markdown(
    f"""
    <div class="hero-wrap">
        <div class="hero-title">JB Insight CRO</div>
        <div class="hero-subtitle">
            계열사별 리스크 데이터를 통합 분석하여 조기경보를 제공하고,
            경영진용 그룹 리스크 브리프를 자동 생성하는 의사결정 보조형 MVP
        </div>
        <div class="info-chip-row">
            <div class="info-chip">기준 월 · {latest_month}</div>
            <div class="info-chip">최고 위험 계열사 · {max_score_company['company_name']}</div>
            <div class="info-chip">최고 점수 · {int(max_score_company['risk_score'])}점</div>
            <div class="info-chip">High 경보 · {high_alert_count}건</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("최고 위험 계열사", max_score_company["company_name"], "그룹 기준 최우선 모니터링 대상")
with c2:
    metric_card("최고 리스크 점수", f"{int(max_score_company['risk_score'])}점", max_score_company["risk_level"])
with c3:
    metric_card("전체 경보 건수", f"{len(alerts_df)}건", f"High {high_alert_count}건 포함")
with c4:
    metric_card("평균 리스크 점수", f"{avg_score}점", "계열사 평균 위험 수준")

st.markdown("### 핵심 모니터링")
tab1, tab2, tab3 = st.tabs(["리스크 랭킹", "조기경보", "보고서 & Q&A"])

with tab1:
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">계열사별 리스크 랭킹</div>', unsafe_allow_html=True)
        ranked = filtered_risk[
            [
                "company_name",
                "company_type",
                "risk_score",
                "risk_level",
                "delinquency_change_pct",
                "complaints_change_pct",
                "abnormal_events_change_pct",
                "real_estate_change_pct",
                "sme_change_pct",
                "top_drivers_text",
            ]
        ].sort_values("risk_score", ascending=False)
        ranked = ranked.rename(
            columns={
                "company_name": "계열사",
                "company_type": "유형",
                "risk_score": "리스크 점수",
                "risk_level": "위험 단계",
                "delinquency_change_pct": "연체율 증감(%)",
                "complaints_change_pct": "민원 증감(%)",
                "abnormal_events_change_pct": "이상 이벤트 증감(%)",
                "real_estate_change_pct": "부동산 익스포저 증감(%)",
                "sme_change_pct": "SME 익스포저 증감(%)",
                "top_drivers_text": "주요 위험 요인",
            }
        )
        st.dataframe(ranked, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">계열사별 리스크 점수</div>', unsafe_allow_html=True)
        fig = px.bar(
            filtered_risk.sort_values("risk_score", ascending=True),
            x="risk_score",
            y="company_name",
            color="risk_level",
            text="risk_score",
            orientation="h",
            color_discrete_map={"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="small-title">월별 지표 추이</div>', unsafe_allow_html=True)
    metric_choice = st.selectbox(
        "추이 지표 선택",
        [
            "delinquency_rate",
            "complaints",
            "abnormal_events",
            "exposure_real_estate",
            "exposure_sme",
        ],
        index=0,
    )
    metric_label_map = {
        "delinquency_rate": "연체율",
        "complaints": "민원 건수",
        "abnormal_events": "이상 이벤트 수",
        "exposure_real_estate": "부동산 익스포저",
        "exposure_sme": "중소기업 익스포저",
    }
    trend_fig = px.line(
        filtered_metrics.sort_values("date"),
        x="date",
        y=metric_choice,
        color="company_name",
        markers=True,
        title=f"월별 {metric_label_map[metric_choice]} 추이",
    )
    trend_fig.update_layout(height=380, margin=dict(l=0, r=0, t=45, b=0))
    st.plotly_chart(trend_fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    left, right = st.columns([1.05, 1])
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">우선 대응 조기경보</div>', unsafe_allow_html=True)
        if filtered_alerts.empty:
            st.info("표시할 경보가 없습니다.")
        else:
            for _, row in filtered_alerts.head(6).iterrows():
                render_alert_card(row)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">최근 리스크 로그</div>', unsafe_allow_html=True)
        log_view = filtered_logs.sort_values("date", ascending=False).rename(
            columns={
                "date": "일자",
                "company_name": "계열사",
                "issue_type": "이슈 유형",
                "severity": "심각도",
                "description": "내용",
            }
        )
        st.dataframe(log_view, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    left, right = st.columns([1.05, 0.95])
    with left:
        st.markdown('<div class="section-card report-box">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">경영진 보고서 자동 생성</div>', unsafe_allow_html=True)
        if st.button("경영진 보고서 생성", use_container_width=True):
            st.session_state["executive_report"] = generate_executive_report(risk_df, alerts_df, latest_month)
        if "executive_report" in st.session_state:
            st.text_area("자동 생성 보고서", st.session_state["executive_report"], height=360)
        else:
            st.caption("버튼을 누르면 경영진용 그룹 리스크 브리프가 생성됩니다.")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">AI Q&A</div>', unsafe_allow_html=True)
        if "qa_answer" in st.session_state:
            st.success(st.session_state["qa_answer"])
        else:
            st.caption("좌측 사이드바에서 데모 질문을 선택해 실행하세요.")

        if not filtered_risk.empty:
            company_row = filtered_risk.sort_values("risk_score", ascending=False).iloc[0]
            st.markdown("#### 주요 위험 요인")
            for driver in company_row["top_drivers"].split("|"):
                if driver.strip():
                    st.markdown(f"- {driver.strip()}")
        st.markdown('</div>', unsafe_allow_html=True)

st.caption("샘플 데이터 기반 데모 · Streamlit MVP · JB Insight CRO")
