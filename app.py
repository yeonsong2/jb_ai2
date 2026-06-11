from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from risk_engine import (
    answer_question,
    calculate_company_risk,
    detect_alerts,
    generate_delinquency_reason_report,
    generate_executive_report,
    get_company_comparison,
    get_delinquency_snapshot,
    get_enterprise_portfolio_summary,
    get_segment_detail_table,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
METRICS_PATH = DATA_DIR / "sample_risk_metrics.csv"
LOGS_PATH = DATA_DIR / "sample_risk_logs.csv"
DRIVERS_PATH = DATA_DIR / "sample_delinquency_drivers.csv"
SEGMENT_PATH = DATA_DIR / "sample_segment_metrics.csv"

st.set_page_config(page_title="JB Insight CRO", page_icon="📊", layout="wide")

CUSTOM_CSS = """
<style>
    .stApp {background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 52%, #f8fafc 100%);}
    .block-container {padding-top: 1rem; padding-bottom: 2rem; max-width: 1480px;}
    .hero-wrap {background: radial-gradient(circle at top left, rgba(96,165,250,0.22), transparent 28%), linear-gradient(135deg, #0b132b 0%, #102a63 48%, #0f4c81 100%); border-radius: 28px; padding: 34px 34px 28px 34px; color: white; box-shadow: 0 18px 50px rgba(15,23,42,0.22); margin-bottom: 18px; border: 1px solid rgba(255,255,255,0.08);}
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


@st.cache_data
def build_dashboard_data():
    metrics, logs, drivers, segments = load_data()
    risk = calculate_company_risk(metrics, logs, drivers)
    alerts = detect_alerts(metrics, logs)
    comparison = get_company_comparison(risk)
    return metrics, logs, drivers, segments, risk, alerts, comparison


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


metrics_df, logs_df, drivers_df, segment_df, risk_df, alerts_df, comparison_data = build_dashboard_data()
latest_date = metrics_df["date"].max()
latest_month = latest_date.strftime("%Y-%m")

with st.sidebar:
    st.header("분석 설정")
    company_options = sorted(metrics_df["company_name"].unique().tolist())
    selected_company = st.selectbox("기업금융 상세 분석 계열사", company_options, index=0)
    severity_filter = st.multiselect("경보 심각도", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
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
        st.session_state["qa_answer"] = answer_question(demo_question, risk_df, alerts_df, metrics_df)
    if st.button("연체율 원인 보고서 생성", use_container_width=True):
        st.session_state["reason_report"] = generate_delinquency_reason_report(metrics_df, drivers_df, segment_df, selected_company)
        st.session_state["reason_report_company"] = selected_company
    st.caption("기업금융 중심 고도화 버전 · PF / 기업대출 / 담보대출 세분화")

selected_snapshot = get_delinquency_snapshot(risk_df, selected_company)
selected_risk_row = risk_df[risk_df["company_name"] == selected_company].iloc[0]
segment_table = get_segment_detail_table(segment_df, selected_company)
portfolio_summary = get_enterprise_portfolio_summary(segment_df, selected_company)
filtered_alerts = alerts_df[alerts_df["severity"].isin(severity_filter)].copy()
max_score_company = risk_df.sort_values("risk_score", ascending=False).iloc[0]
high_alert_count = len(alerts_df[alerts_df["severity"] == "High"])
avg_score = round(risk_df["risk_score"].mean(), 1)

st.markdown(
    f"""
    <div class="hero-wrap">
        <div class="hero-kicker">Enterprise Finance Risk Intelligence</div>
        <div class="hero-title">JB Insight CRO</div>
        <div class="hero-subtitle">
            기업금융 포트폴리오를 중심으로 PF, 기업 운전자금, 담보부 대출, 무역금융까지 세분화해 분석하는
            그룹 리스크 인텔리전스 대시보드입니다. 전월 대비 변화와 3개월 평균 이탈을 동시에 보여주고,
            연체율 상승·하락 원인을 경영진 문체로 요약하며, 세그먼트 단위 Drill-down까지 제공합니다.
        </div>
        <div class="info-chip-row">
            <div class="info-chip">기준 월 · {latest_month}</div>
            <div class="info-chip">상세 분석 계열사 · {selected_company}</div>
            <div class="info-chip">최고 위험 계열사 · {max_score_company['company_name']}</div>
            <div class="info-chip">High 경보 · {high_alert_count}건</div>
            <div class="info-chip">PF 비중 · {portfolio_summary['pf_share']}%</div>
            <div class="info-chip">담보 기반 비중 · {portfolio_summary['secured_share']}%</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

row1 = st.columns(4)
with row1[0]:
    metric_card("최고 위험 계열사", max_score_company["company_name"], "그룹 기준 최우선 모니터링 대상", "Group View")
with row1[1]:
    metric_card("평균 리스크 점수", f"{avg_score}점", "계열사 평균 위험 수준", "Risk Score")
with row1[2]:
    metric_card(f"{selected_company} 현재 연체율", f"{selected_snapshot['current_rate']:.2f}%", selected_snapshot['headline'], "Credit View")
with row1[3]:
    metric_card("전체 경보 건수", f"{len(alerts_df)}건", f"High {high_alert_count}건 포함", "Alert Monitor")

row2 = st.columns(4)
with row2[0]:
    metric_card("전월 대비 변화", f"{selected_snapshot['mom_change_pp']:+.2f}%p", f"변화율 {selected_snapshot['mom_change_pct']}%", "MoM")
with row2[1]:
    metric_card("3개월 평균 대비", f"{selected_snapshot['vs_3m_avg_pp']:+.2f}%p", f"기준 평균 {selected_snapshot['trailing_3m_avg']:.2f}%", "3M Avg")
with row2[2]:
    metric_card("개선 사례", comparison_data['best_company'], f"{comparison_data['best_change_pp']:+.2f}%p · {comparison_data['best_summary']}", "Best Case")
with row2[3]:
    metric_card("악화 사례", comparison_data['worst_company'], f"{comparison_data['worst_change_pp']:+.2f}%p · {comparison_data['worst_summary']}", "Watchlist")

st.markdown("### 핵심 모니터링")
tab1, tab2, tab3, tab4 = st.tabs(["그룹 현황", "조기경보 & 추이", "기업금융 세부 포트폴리오", "보고서 & Q&A"])

with tab1:
    left, right = st.columns([1.1, 0.9])
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">계열사별 리스크 랭킹</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">전월 대비 변화, 3개월 평균 대비 이탈, 드라이버 요약을 함께 제공합니다.</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="small-title">계열사별 리스크 점수</div>', unsafe_allow_html=True)
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
        fig.update_layout(height=420, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="small-title">계열사별 개선/악화 비교</div>', unsafe_allow_html=True)
    st.dataframe(comparison_data['trend_table'], use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">우선 대응 조기경보</div>', unsafe_allow_html=True)
        if filtered_alerts.empty:
            st.info("표시할 경보가 없습니다.")
        else:
            for _, row in filtered_alerts.head(8).iterrows():
                render_alert_card(row)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">월별 지표 추이</div>', unsafe_allow_html=True)
        metric_choice = st.selectbox("추이 지표 선택", ["delinquency_rate", "complaints", "abnormal_events", "exposure_real_estate", "exposure_sme"], index=0)
        metric_label_map = {
            "delinquency_rate": "연체율",
            "complaints": "민원 건수",
            "abnormal_events": "이상 이벤트 수",
            "exposure_real_estate": "부동산 익스포저",
            "exposure_sme": "중소기업 익스포저",
        }
        trend_fig = px.line(metrics_df.sort_values("date"), x="date", y=metric_choice, color="company_name", markers=True, title=f"월별 {metric_label_map[metric_choice]} 추이")
        trend_fig.update_layout(height=410, margin=dict(l=0, r=0, t=44, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(trend_fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    top_left, top_right = st.columns([0.95, 1.05])
    with top_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="small-title">{selected_company} 카드형 요약</div>', unsafe_allow_html=True)
        render_reason_box("경영진 해석", selected_snapshot['headline'], positive=(selected_snapshot['mom_change_pp'] <= 0))
        render_reason_box("연체율 하락/개선 이유", selected_snapshot['positive_driver_summary'], positive=True)
        render_reason_box("연체율 상승/악화 이유", selected_snapshot['negative_driver_summary'], positive=False)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="small-title">{selected_company} 포트폴리오 핵심 요약</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="premium-note">PF 비중 <b>{portfolio_summary["pf_share"]}%</b> · 담보 기반 비중 <b>{portfolio_summary["secured_share"]}%</b><br>가장 큰 세그먼트는 <b>{portfolio_summary["largest_balance_segment"]}</b>이며 잔액은 <b>{portfolio_summary["largest_balance"]}</b>입니다.<br>가장 악화된 세그먼트는 <b>{portfolio_summary["worst_segment"]}</b>({portfolio_summary["worst_change_pp"]:+.2f}%p), 가장 개선된 세그먼트는 <b>{portfolio_summary["best_segment"]}</b>({portfolio_summary["best_change_pp"]:+.2f}%p)입니다.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with top_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="small-title">{selected_company} 세그먼트 상세 변화</div>', unsafe_allow_html=True)
        st.dataframe(segment_table, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    mid_left, mid_right = st.columns([1, 1])
    with mid_left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">세그먼트별 연체율 변화</div>', unsafe_allow_html=True)
        seg_fig = px.bar(
            segment_table,
            x="세그먼트",
            y="연체율 변화(%p)",
            color="담보유형",
            text="연체율 변화(%p)",
            title="PF · 기업대출 · 담보대출 세그먼트 변화"
        )
        seg_fig.update_layout(height=380, margin=dict(l=0, r=0, t=44, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(seg_fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with mid_right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">세그먼트 리스크 포지셔닝</div>', unsafe_allow_html=True)
        scatter = px.scatter(
            segment_table,
            x="잔액 변화",
            y="연체율 변화(%p)",
            size="현재 잔액",
            color="담보유형",
            hover_name="세그먼트",
            symbol="업종",
            title="잔액 증가와 연체율 변화의 동시 모니터링"
        )
        scatter.update_layout(height=380, margin=dict(l=0, r=0, t=44, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(scatter, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    left, right = st.columns([1.05, 0.95])
    with left:
        st.markdown('<div class="section-card report-box">', unsafe_allow_html=True)
        st.markdown(f'<div class="small-title">{selected_company} 임원 보고용 연체율 분석</div>', unsafe_allow_html=True)
        if "reason_report" not in st.session_state or st.session_state.get("reason_report_company") != selected_company:
            st.session_state["reason_report"] = generate_delinquency_reason_report(metrics_df, drivers_df, segment_df, selected_company)
            st.session_state["reason_report_company"] = selected_company
        if st.button("선택 계열사 기준 보고서 새로고침", use_container_width=True):
            st.session_state["reason_report"] = generate_delinquency_reason_report(metrics_df, drivers_df, segment_df, selected_company)
            st.session_state["reason_report_company"] = selected_company
        st.text_area("임원 보고용 연체율 분석", st.session_state["reason_report"], height=460)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card report-box">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">경영진 그룹 브리프</div>', unsafe_allow_html=True)
        if st.button("경영진 보고서 생성", use_container_width=True):
            st.session_state["executive_report"] = generate_executive_report(risk_df, alerts_df, latest_month)
        if "executive_report" not in st.session_state:
            st.session_state["executive_report"] = generate_executive_report(risk_df, alerts_df, latest_month)
        st.text_area("자동 생성 보고서", st.session_state["executive_report"], height=300)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">AI Q&A</div>', unsafe_allow_html=True)
        if "qa_answer" in st.session_state:
            st.success(st.session_state["qa_answer"])
        else:
            st.caption("좌측 사이드바에서 데모 질문을 선택해 실행하세요.")
        st.markdown("#### 현재 선택 계열사 핵심 요인")
        for item in selected_risk_row["top_drivers"].split("|"):
            st.markdown(f"- {item}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">기업금융 포커스 포인트</div>', unsafe_allow_html=True)
        st.markdown("- PF / 프로젝트금융은 만기 구조와 차환 부담을 별도 관리")
        st.markdown("- 기업 운전자금대출은 업종 편중과 차주군 질 변화 동시 점검")
        st.markdown("- 담보대출은 담보가치 재평가와 회수정책의 실효성을 함께 추적")
        st.markdown('</div>', unsafe_allow_html=True)

st.caption("샘플 데이터 기반 데모 · 기업금융 중심 세분화(PF, 기업 운전자금, 담보대출, 무역금융) 및 고급형 UI 적용")
