import sys

import pandas as pd
import streamlit as st

from constants import EXPECTED_PYTHON


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


def render_deploy_status_banner(metrics_df, risk_df, alerts_df, latest_month: str):
    metrics_rows = len(metrics_df) if isinstance(metrics_df, pd.DataFrame) else 0
    risk_rows = len(risk_df) if isinstance(risk_df, pd.DataFrame) else 0
    alerts_rows = len(alerts_df) if isinstance(alerts_df, pd.DataFrame) else 0
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
            <div class="status-chip">expected python · {EXPECTED_PYTHON}</div>
            <div class="status-chip">runtime python · {runtime_python}</div>
            <div class="status-chip">healthcheck · {driver}</div>
        </div>
    </div>
    """
    st.markdown(banner, unsafe_allow_html=True)


def render_healthcheck_summary(metrics_df, logs_df, drivers_df, segment_df, risk_df, alerts_df):
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
    st.caption(f"클라우드 배포 시 Python {EXPECTED_PYTHON} 고정을 권장합니다.")
