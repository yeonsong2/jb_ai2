import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from constants import (
    APP_ICON,
    APP_TITLE,
    BASE_DIR,
    DATA_DIR,
    DEMO_MODES,
    DRIVERS_PATH,
    FOCUS_MODE_TO_DEMO,
    LOGS_PATH,
    METRICS_PATH,
    REQUIRED_COLUMNS,
    SEGMENT_PATH,
)
from data_loader import build_dashboard_data, load_dataframes, validate_required_columns
from healthcheck import (
    ensure_dataframe_columns,
    fallback_comparison_data,
    fallback_portfolio_summary,
    fallback_snapshot,
    render_deploy_status_banner,
    render_healthcheck_summary,
    stop_with_deploy_diagnostics,
)
from llm_service import (
    answer_exec_question_with_llm,
    build_llm_context,
    generate_executive_report_with_llm,
    generate_orchestrator_brief,
    generate_specialist_opinion,
    interpret_scenario_with_llm,
)
from pdf_export import build_company_report_pdf, build_group_brief_pdf
from risk_engine import (
    answer_question,
    generate_delinquency_reason_report,
    generate_executive_report,
    get_action_item_table,
    get_agent_execution_table,
    get_delinquency_snapshot,
    get_enterprise_portfolio_summary,
    get_segment_detail_table,
    simulate_what_if_scenario,
)
from ui_components import (
    apply_chart_theme,
    build_risk_heatmap_figure,
    build_segment_heatmap_figure,
    inject_custom_css,
    metric_card,
    render_action_card,
    render_alert_card,
    render_insight_panel,
    render_reason_box,
    render_signal_card,
)

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
inject_custom_css()

try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    api_key = os.environ.get("OPENAI_API_KEY")

api_key_configured = bool(api_key)


@st.cache_data
def load_data():
    return load_dataframes(METRICS_PATH, LOGS_PATH, DRIVERS_PATH, SEGMENT_PATH)


@st.cache_data
def load_demo_llm_payloads():
    payload_path = DATA_DIR / "demo_llm_payloads.json"
    with payload_path.open("r", encoding="utf-8") as file:
        return json.load(file)


class _SafeFormatDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"



def _build_demo_render_context(llm_context=None, scenario_result=None, question=""):
    llm_context = llm_context or {}
    snapshot = llm_context.get("snapshot", {}) or {}
    portfolio = llm_context.get("portfolio_summary", {}) or {}
    alerts = llm_context.get("alerts", []) or []
    context = {
        "selected_company": llm_context.get("selected_company", st.session_state.get("selected_company", "JB우리캐피탈")),
        "focus_mode": llm_context.get("focus_mode", st.session_state.get("focus_mode", "경영진 보고")),
        "latest_month": llm_context.get("latest_month", "N/A"),
        "current_rate": float(snapshot.get("current_rate", 0.0) or 0.0),
        "mom_change_pp": float(snapshot.get("mom_change_pp", 0.0) or 0.0),
        "vs_3m_avg_pp": float(snapshot.get("vs_3m_avg_pp", 0.0) or 0.0),
        "negative_driver_summary": snapshot.get("negative_driver_summary", "악화 요인 데이터 없음"),
        "headline": snapshot.get("headline", "핵심 리스크 재점검이 필요합니다."),
        "worst_segment": portfolio.get("worst_segment", "핵심 세그먼트"),
        "largest_balance_segment": portfolio.get("largest_balance_segment", "최대 익스포저 세그먼트"),
        "pf_share": portfolio.get("pf_share", 0.0),
        "secured_share": portfolio.get("secured_share", 0.0),
        "alerts_count": len(alerts),
        "question": question,
        "projected_rate": 0.0,
        "stress_delta": 0.0,
    }
    if scenario_result:
        context["projected_rate"] = float(scenario_result.get("projected_rate", 0.0) or 0.0)
        context["stress_delta"] = float(scenario_result.get("stress_delta", 0.0) or 0.0)
    return context



def _render_demo_template(template, llm_context=None, scenario_result=None, question=""):
    if not template:
        return None
    context = _build_demo_render_context(llm_context=llm_context, scenario_result=scenario_result, question=question)
    return str(template).format_map(_SafeFormatDict(context))



def _get_demo_payload(llm_context=None):
    payloads = load_demo_llm_payloads()
    llm_context = llm_context or {}
    selected_company = llm_context.get("selected_company", st.session_state.get("selected_company", "JB우리캐피탈"))
    focus_mode = llm_context.get("focus_mode", st.session_state.get("focus_mode", "경영진 보고"))
    exact_key = f"{selected_company}|{focus_mode}"
    focus_key = f"__focus__|{focus_mode}"

    merged_payload = dict(payloads.get("__default__", {}))
    merged_payload.update(payloads.get(focus_key, {}))
    merged_payload.update(payloads.get(exact_key, {}))

    merged_qa = dict(payloads.get("__default__", {}).get("qa_answers", {}))
    merged_qa.update(payloads.get(focus_key, {}).get("qa_answers", {}))
    merged_qa.update(payloads.get(exact_key, {}).get("qa_answers", {}))
    merged_payload["qa_answers"] = merged_qa
    return merged_payload



def _get_demo_cached_text(field_name, llm_context=None, question="", scenario_result=None):
    payload = _get_demo_payload(llm_context=llm_context)
    if field_name == "qa_answer":
        qa_answers = payload.get("qa_answers", {})
        template = qa_answers.get(question) or qa_answers.get("__default__")
        return _render_demo_template(template, llm_context=llm_context, scenario_result=scenario_result, question=question)
    template = payload.get(field_name)
    return _render_demo_template(template, llm_context=llm_context, scenario_result=scenario_result, question=question)



def _generation_label():
    return "DEMO CACHE" if st.session_state.get("llm_cache_demo_mode", False) else pd.Timestamp.now().strftime("%H:%M:%S")


FOCUS_KEYWORDS = {
    "PF 집중 점검": ["pf", "프로젝트", "브릿지", "본pf", "차환", "project"],
    "기업대출 점검": ["기업", "sme", "법인", "운전자금", "시설자금", "매출채권", "무역금융"],
    "담보·회수 점검": ["담보", "회수", "재평가", "리스케줄링", "recovery", "collateral"],
    "경영진 보고": ["경영", "보고", "브리프", "비교", "benchmark", "executive", "orchestrator"],
}

FOCUS_DEFAULT_METRIC = {
    "그룹 스캔": "delinquency_rate",
    "PF 집중 점검": "exposure_real_estate",
    "기업대출 점검": "exposure_sme",
    "담보·회수 점검": "exposure_real_estate",
    "경영진 보고": "delinquency_rate",
}


FOCUS_TAB_LABELS = {
    "그룹 스캔": ["1. 그룹 스캔", "2. 조기경보 · 계열 비교", "3. 핵심 세그먼트", "4. 보고 · Q&A"],
    "PF 집중 점검": ["1. PF 브리프", "2. PF 경보 · 비교", "3. PF 세부진단", "4. PF 보고 · Q&A"],
    "기업대출 점검": ["1. 기업대출 브리프", "2. 기업대출 경보 · 비교", "3. 기업대출 세부진단", "4. 기업대출 보고 · Q&A"],
    "담보·회수 점검": ["1. 담보·회수 브리프", "2. 담보·회수 경보 · 비교", "3. 담보·회수 세부진단", "4. 담보·회수 보고 · Q&A"],
    "경영진 보고": ["1. 경영진 요약", "2. 핵심 경보 · 계열 비교", "3. 시나리오 · 세그먼트", "4. 보고서 · Q&A"],
}

FOCUS_BANNER_MESSAGES = {
    "그룹 스캔": "그룹 전체 비교와 High·Medium 경보 중심으로 우선 점검 대상을 빠르게 식별하는 모드입니다.",
    "PF 집중 점검": "PF·브릿지론·차환 리스크 관련 데이터만 우선 재구성해 세부 진단과 시나리오를 강조하는 모드입니다.",
    "기업대출 점검": "기업대출·SME·운전자금 관련 데이터만 우선 재구성해 차주군/업종 리스크를 점검하는 모드입니다.",
    "담보·회수 점검": "담보 재평가·회수 지연·회수정책 관련 데이터만 우선 재구성해 실행 과제를 확인하는 모드입니다.",
    "경영진 보고": "경영진 보고용 핵심 메시지와 실행 과제, 질의응답 초안을 우선 노출하는 모드입니다.",
}

FOCUS_QUESTION_OPTIONS = {
    "그룹 스캔": [
        "왜 {selected_company}이 최우선 점검 대상인가",
        "그룹 내 비교 가능한 개선 사례는 어디인가",
        "이번 달 즉시 실행해야 할 조치는 무엇인가",
        "가장 먼저 점검해야 할 경보는 무엇인가",
    ],
    "PF 집중 점검": [
        "PF 차환 리스크의 핵심 근거는 무엇인가",
        "브릿지론과 본PF 중 어디를 먼저 점검해야 하는가",
        "PF 관련 즉시 실행 조치는 무엇인가",
        "스트레스 확대 시 PF에서 가장 먼저 흔들리는 구간은 어디인가",
    ],
    "기업대출 점검": [
        "기업대출 포트폴리오에서 가장 취약한 차주군은 어디인가",
        "SME 업황 악화가 연체율에 미치는 영향은 무엇인가",
        "기업대출 관련 즉시 실행 조치는 무엇인가",
        "업종 편중 리스크를 어떻게 설명해야 하는가",
    ],
    "담보·회수 점검": [
        "담보 재평가가 가장 시급한 구간은 어디인가",
        "회수 단계 전환이 늦어진 원인은 무엇인가",
        "담보·회수 관련 즉시 실행 조치는 무엇인가",
        "회수정책 우선순위를 어떻게 설명해야 하는가",
    ],
    "경영진 보고": [
        "왜 {selected_company}이 최우선 점검 대상인가",
        "PF 외 추가 악화 축은 무엇인가",
        "이번 달 즉시 실행 조치는 무엇인가",
        "그룹 내 비교 가능한 개선 사례는 어디인가",
    ],
}


def _get_focus_tab_labels(focus_mode):
    return FOCUS_TAB_LABELS.get(focus_mode, FOCUS_TAB_LABELS["경영진 보고"])



def _get_focus_question_options(selected_company, focus_mode):
    templates = FOCUS_QUESTION_OPTIONS.get(focus_mode, FOCUS_QUESTION_OPTIONS["경영진 보고"])
    return [template.format(selected_company=selected_company) for template in templates]



def _focus_keyword_match(df, columns, keywords):
    if df is None or not isinstance(df, pd.DataFrame) or df.empty or not keywords:
        return pd.DataFrame() if df is None else df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame()
    usable_columns = [col for col in columns if col in df.columns]
    if not usable_columns:
        return pd.DataFrame(columns=getattr(df, 'columns', []))
    lowered_keywords = [str(keyword).lower() for keyword in keywords]
    mask = pd.Series(False, index=df.index)
    for col in usable_columns:
        series = df[col].fillna("").astype(str).str.lower()
        for keyword in lowered_keywords:
            mask = mask | series.str.contains(keyword, regex=False)
    return df[mask].copy()



def _get_focus_view(focus_mode, filtered_alerts, selected_driver_rows, segment_table, action_item_display, ranking_table):
    focus_alerts = filtered_alerts.copy() if isinstance(filtered_alerts, pd.DataFrame) else pd.DataFrame()
    focus_driver_rows = selected_driver_rows.copy() if isinstance(selected_driver_rows, pd.DataFrame) else pd.DataFrame()
    focus_segment_table = segment_table.copy() if isinstance(segment_table, pd.DataFrame) else pd.DataFrame()
    focus_actions = action_item_display.copy() if isinstance(action_item_display, pd.DataFrame) else pd.DataFrame()
    focus_ranking_table = ranking_table.copy() if isinstance(ranking_table, pd.DataFrame) else pd.DataFrame()

    keywords = FOCUS_KEYWORDS.get(focus_mode, [])
    if focus_mode != "그룹 스캔":
        filtered = _focus_keyword_match(focus_alerts, ["alert_type", "detail", "recommended_action"], keywords)
        if not filtered.empty:
            focus_alerts = filtered
        filtered = _focus_keyword_match(focus_driver_rows, ["driver_name", "description"], keywords)
        if not filtered.empty:
            focus_driver_rows = filtered
        filtered = _focus_keyword_match(focus_segment_table, ["세그먼트", "담보유형", "업종"], keywords)
        if not filtered.empty:
            focus_segment_table = filtered
        filtered = _focus_keyword_match(focus_actions, ["담당 영역", "액션 아이템", "목적"], keywords)
        if not filtered.empty:
            focus_actions = filtered

    focus_segment_table_display = focus_segment_table.copy()
    if not focus_segment_table_display.empty and "연체율 변화(%p)" in focus_segment_table_display.columns:
        focus_segment_table_display["위험도"] = focus_segment_table_display["연체율 변화(%p)"].apply(lambda x: "High" if x >= 0.30 else "Medium" if x >= 0.10 else "Low")
        focus_segment_table_display["점검 필요"] = focus_segment_table_display["연체율 변화(%p)"].apply(lambda x: "즉시" if x >= 0.30 else "관찰" if x >= 0.10 else "안정")
        display_cols = [col for col in ["세그먼트", "현재 연체율", "연체율 변화(%p)", "위험도", "점검 필요"] if col in focus_segment_table_display.columns]
        focus_segment_table_display = focus_segment_table_display[display_cols].head(7)

    if focus_mode == "그룹 스캔":
        focus_card = {"label": "즉시 점검 경보", "value": f"{len(focus_alerts)}건", "caption": "High·Medium 경보 기준", "badge": "Alert"}
        stress_defaults = {"pf": 0.30, "collateral": 0.20, "sme": 0.15}
    elif focus_mode == "PF 집중 점검":
        focus_card = {"label": "PF 관련 신호", "value": f"{len(focus_driver_rows)}건", "caption": "PF·브릿지론·차환 관련", "badge": "PF"}
        stress_defaults = {"pf": 0.45, "collateral": 0.15, "sme": 0.10}
    elif focus_mode == "기업대출 점검":
        focus_card = {"label": "기업대출 점검 세그먼트", "value": f"{len(focus_segment_table_display)}개", "caption": "SME·운전자금 중심", "badge": "Loan"}
        stress_defaults = {"pf": 0.15, "collateral": 0.10, "sme": 0.35}
    elif focus_mode == "담보·회수 점검":
        focus_card = {"label": "담보·회수 액션", "value": f"{len(focus_actions)}건", "caption": "담보 재평가·회수정책 중심", "badge": "Recovery"}
        stress_defaults = {"pf": 0.10, "collateral": 0.40, "sme": 0.10}
    else:
        focus_card = {"label": "보고 핵심 과제", "value": f"{len(focus_actions.head(5))}건", "caption": "임원 보고용 우선 과제", "badge": "Exec"}
        stress_defaults = {"pf": 0.30, "collateral": 0.20, "sme": 0.15}

    return {
        "alerts": focus_alerts,
        "driver_rows": focus_driver_rows,
        "top_signals": focus_driver_rows.head(3).copy() if not focus_driver_rows.empty else pd.DataFrame(),
        "actions": focus_actions,
        "quick_actions": focus_actions.head(3).copy() if not focus_actions.empty else pd.DataFrame(),
        "segment_table": focus_segment_table,
        "segment_table_display": focus_segment_table_display,
        "ranking_table": focus_ranking_table,
        "tab_labels": _get_focus_tab_labels(focus_mode),
        "banner_message": FOCUS_BANNER_MESSAGES.get(focus_mode, FOCUS_BANNER_MESSAGES["경영진 보고"]),
        "focus_card": focus_card,
        "stress_defaults": stress_defaults,
    }



def _build_rule_based_orchestrator_brief(llm_context):
    snapshot = llm_context.get("snapshot", {})
    portfolio = llm_context.get("portfolio_summary", {})
    actions = llm_context.get("action_items", [])
    alerts = llm_context.get("alerts", [])
    action_lines = [
        f"- {item.get('시점', '오늘')} · {item.get('액션 아이템', '기본 점검')}"
        for item in actions[:3]
    ]
    if not action_lines:
        action_lines = [
            "- 오늘 · 차주 리스트와 담보 재평가 대상 우선 점검",
            "- 이번 주 · 만기집중 PF 차환 일정 재검토",
            "- 이번 달 · 회수 우선순위와 한도 운영 기준 재정비",
        ]
    return f'''[핵심 리스크]
- {llm_context.get("selected_company", "대상 회사")}의 핵심 위험은 {portfolio.get("worst_segment", "핵심 세그먼트")} 중심의 연체 압력 확대입니다.
- 현재 연체율 {snapshot.get("current_rate", 0.0):.2f}%, 전월 대비 {snapshot.get("mom_change_pp", 0.0):+.2f}%p, 3개월 평균 대비 {snapshot.get("vs_3m_avg_pp", 0.0):+.2f}%p입니다.

[주요 원인]
- {snapshot.get("negative_driver_summary", "악화 요인 데이터 없음")}
- 최대 익스포저 세그먼트는 {portfolio.get("largest_balance_segment", "데이터 없음")}이며, 취약 구간은 {portfolio.get("worst_segment", "데이터 없음")}입니다.
- 현재 점검 대상 경보는 {len(alerts)}건입니다.

[즉시 조치]
{chr(10).join(action_lines[:3])}

[경영 판단 포인트]
- PF 비중 {portfolio.get("pf_share", 0.0)}%, 담보 기반 익스포저 {portfolio.get("secured_share", 0.0)}% 구조에서는 차환 일정과 담보 재평가를 같은 회의 안건으로 묶는 편이 적절합니다.
- 단기 대응은 차주 리스트 재점검, 담보 재평가 대상 선별, 회수 우선순위 조정 순으로 정리하는 것이 적절합니다.'''


def _build_rule_based_specialist_note(agent_name, focus, llm_context):
    snapshot = llm_context.get("snapshot", {})
    portfolio = llm_context.get("portfolio_summary", {})
    if "PF" in agent_name:
        current_judgement = f"{portfolio.get('worst_segment', '핵심 세그먼트')}의 차환 부담이 현재 PF 관제의 중심입니다."
        evidence = snapshot.get("negative_driver_summary", "PF 관련 악화 요인이 관찰됩니다.")
        action = f"{portfolio.get('worst_segment', 'PF 세그먼트')} 만기 구조와 차주별 차환 가능성부터 재확인해야 합니다."
        memo = "본PF와 브릿지론을 분리해 우선순위를 잡으면 대응 속도가 빨라집니다."
    elif "Collateral" in agent_name:
        current_judgement = f"담보 방어력은 {portfolio.get('worst_segment', '취약 세그먼트')} 점검과 함께 봐야 합니다."
        evidence = f"담보 기반 익스포저 비중은 {portfolio.get('secured_share', 0.0)}%이며, 회수 지연 신호와 함께 확인이 필요합니다."
        action = "담보 재평가 대상과 회수 우선순위 차주를 분리해서 점검해야 합니다."
        memo = "회수정책 조정은 차주 리스트 재점검 뒤에 붙는 것이 자연스럽습니다."
    else:
        current_judgement = snapshot.get("headline", "핵심 위험 재점검이 필요합니다.")
        evidence = snapshot.get("negative_driver_summary", focus)
        action = "우선 점검 대상과 실행 과제를 동시에 정리해야 합니다."
        memo = "전월 대비 변화와 3개월 평균 이탈을 함께 보는 구조가 적절합니다."
    return f'''[현재 판단]
{current_judgement}

[핵심 근거]
{evidence}

[우선 점검 항목]
{action}

[실무 메모]
{memo}'''


def _build_rule_based_scenario_note(llm_context, scenario_result):
    portfolio = llm_context.get("portfolio_summary", {}) or {}
    snapshot = llm_context.get("snapshot", {}) or {}
    focus_mode = llm_context.get("focus_mode", "경영진 보고")
    base_rate = float(scenario_result.get("base_rate", snapshot.get("current_rate", 0.0)) or 0.0)
    projected_rate = float(scenario_result.get("projected_rate", 0.0) or 0.0)
    stress_delta = float(scenario_result.get("stress_delta", 0.0) or 0.0)
    projected_risk_level = scenario_result.get("projected_risk_level", "N/A")
    projected_risk_score = float(scenario_result.get("projected_risk_score", 0.0) or 0.0)
    impact_summary = scenario_result.get("impact_summary", "세부 영향 요약 없음")
    worst_segment = portfolio.get("worst_segment", "취약 세그먼트")
    largest_balance_segment = portfolio.get("largest_balance_segment", "최대 익스포저 세그먼트")
    pf_share = float(portfolio.get("pf_share", 0.0) or 0.0)
    secured_share = float(portfolio.get("secured_share", 0.0) or 0.0)

    action_map = {
        "PF 집중 점검": [
            "오늘 · 브릿지론·본PF 만기 도래 건을 분리해 차환 가능 / 연장 협의 / 회수 검토 3단계로 재분류합니다.",
            "이번 주 · 사업장별 분양률·공정률·시공사 신용도 기준으로 PF 취약 리스트를 다시 정렬합니다.",
            "이번 달 · 본PF 전환 지연 사업장과 신규 자금 집행 건을 함께 묶어 경영진 의사결정 안건으로 상정합니다.",
        ],
        "기업대출 점검": [
            "오늘 · 업종 민감 차주와 PF 연계 차주를 분리해 한도 재점검 대상을 확정합니다.",
            "이번 주 · 건설·제조·유통 등 변동성 높은 차주군 중심으로 조기경보 차주 리스트를 재편합니다.",
            "이번 달 · 업종 편중 완화와 담보 보강 필요 차주를 묶어 재약정 후보군을 보고합니다.",
        ],
        "담보·회수 점검": [
            "오늘 · LTV 상위 건과 회수 단계 지연 건을 우선 재평가 대상으로 확정합니다.",
            "이번 주 · 담보 커버리지 부족 차주와 정상화 가능 차주를 분리해 회수 우선순위를 재정렬합니다.",
            "이번 달 · 재평가 결과를 반영해 매각·재약정·법적 조치 후보를 경영진 안건으로 정리합니다.",
        ],
        "그룹 스캔": [
            "오늘 · 최우선 점검 계열사와 동반 악화 계열사를 병렬로 점검합니다.",
            "이번 주 · 그룹 공통 취약 신호와 계열사별 개별 원인을 나눠서 우선순위를 재정렬합니다.",
            "이번 달 · 그룹 차원의 차환·담보·회수 실행 패키지를 통합 보고합니다.",
        ],
        "경영진 보고": [
            "오늘 · 취약 차주 리스트와 만기 도래 건을 우선 재점검합니다.",
            "이번 주 · 담보 재평가 대상과 회수 우선순위 차주를 분리 점검합니다.",
            "이번 달 · 차환 일정, 한도 운영, 회수정책 조정안을 하나의 패키지로 보고합니다.",
        ],
    }
    actions = action_map.get(focus_mode, action_map["경영진 보고"])

    return f'''[시나리오 결과]
- 기준 연체율 {base_rate:.2f}% → 예상 연체율 {projected_rate:.2f}% ({stress_delta:+.2f}%p)
- 예상 위험 단계는 {projected_risk_level}, 예상 리스크 점수는 {projected_risk_score:.1f}입니다.
- 시뮬레이션 요약: {impact_summary}

[우선 점검 대상]
- 1순위 세그먼트는 {worst_segment}입니다.
- 최대 익스포저 세그먼트는 {largest_balance_segment}이며, 충격 확대 시 손실 흡수력 점검이 필요합니다.
- 현재 포트폴리오 구조는 PF 비중 {pf_share:.1f}%, 담보 기반 익스포저 {secured_share:.1f}% 수준이어서 차환·담보·회수 판단을 분리하지 말고 함께 봐야 합니다.

[실무 대응 순서]
- {actions[0]}
- {actions[1]}
- {actions[2]}

[보고 포인트]
- 이번 시나리오는 단순 수치 변동보다 어느 세그먼트와 어떤 실행 과제가 먼저 움직여야 하는지를 보여주는 용도로 활용하는 것이 적절합니다.'''

def safe_generate_reason_report(metrics_df, drivers_df, segment_df, selected_company, llm_context=None):
    if llm_context and st.session_state.get("llm_cache_demo_mode", False):
        text = _get_demo_cached_text("reason_report", llm_context=llm_context)
        if text:
            return text
    if llm_context and api_key_configured:
        text, err = generate_executive_report_with_llm(llm_context)
        if not err and text:
            return text
    try:
        return generate_delinquency_reason_report(metrics_df, drivers_df, segment_df, selected_company)
    except Exception as exc:
        return f"[{selected_company}] 보고서 생성 중 예외가 발생해 핵심 요약만 표시합니다. 상세 오류: {exc}"


def safe_generate_executive_report(risk_df, alerts_df, latest_month, llm_context=None):
    if llm_context and st.session_state.get("llm_cache_demo_mode", False):
        text = _get_demo_cached_text("executive_report", llm_context=llm_context)
        if text:
            return text
    if llm_context and api_key_configured:
        text, err = generate_executive_report_with_llm(llm_context)
        if not err and text:
            return text
    try:
        return generate_executive_report(risk_df, alerts_df, latest_month)
    except Exception as exc:
        return f"[{latest_month}] 그룹 브리프 생성 중 예외가 발생했습니다. 상세 오류: {exc}"


def safe_generate_orchestrator_brief(llm_context):
    if st.session_state.get("llm_cache_demo_mode", False):
        text = _get_demo_cached_text("orchestrator_brief", llm_context=llm_context)
        if text:
            return text
    if api_key_configured:
        text, err = generate_orchestrator_brief(llm_context)
        if not err and text:
            return text
    return _build_rule_based_orchestrator_brief(llm_context)


def safe_generate_specialist_note(agent_name, focus, llm_context):
    if st.session_state.get("llm_cache_demo_mode", False):
        field_name = "early_warning_note"
        if "PF" in agent_name:
            field_name = "pf_agent_note"
        elif "Collateral" in agent_name:
            field_name = "collateral_agent_note"
        text = _get_demo_cached_text(field_name, llm_context=llm_context)
        if text:
            return text
    if api_key_configured:
        text, err = generate_specialist_opinion(agent_name, focus, llm_context)
        if not err and text:
            return text
    return _build_rule_based_specialist_note(agent_name, focus, llm_context)


def safe_generate_ai_executive_report(llm_context):
    if api_key_configured:
        text, err = generate_executive_report_with_llm(llm_context)
        if not err and text:
            return text
    return _build_rule_based_orchestrator_brief(llm_context)


def safe_answer_question(question, risk_df, alerts_df, metrics_df, llm_context=None):
    if llm_context and st.session_state.get("llm_cache_demo_mode", False):
        text = _get_demo_cached_text("qa_answer", llm_context=llm_context, question=question)
        if text:
            return text
    if llm_context and api_key_configured:
        text, err = answer_exec_question_with_llm(question, llm_context)
        if not err and text:
            return text
    try:
        return answer_question(question, risk_df, alerts_df, metrics_df)
    except Exception as exc:
        return f"질의응답 생성 중 예외가 발생했습니다: {exc}"


def safe_interpret_scenario(llm_context, scenario_result):
    if st.session_state.get("llm_cache_demo_mode", False):
        text = _get_demo_cached_text("scenario_agent_note", llm_context=llm_context, scenario_result=scenario_result)
        if text:
            return text
    if api_key_configured:
        text, err = interpret_scenario_with_llm(llm_context, scenario_result)
        if not err and text:
            return text
    return _build_rule_based_scenario_note(llm_context, scenario_result)


def safe_simulate_what_if(selected_company, risk_df, segment_df, pf_stress, collateral_stress, sme_stress):
    try:
        return simulate_what_if_scenario(selected_company, risk_df, segment_df, pf_stress, collateral_stress, sme_stress)
    except Exception as exc:
        return {
            "base_rate": 0.0,
            "projected_rate": 0.0,
            "stress_delta": 0.0,
            "projected_risk_level": "N/A",
            "projected_risk_score": 0.0,
            "impact_summary": f"시뮬레이션 예외: {exc}",
        }


def build_company_trend_figure(metrics_df, selected_company):
    if metrics_df.empty:
        return None
    company_df = metrics_df[metrics_df["company_name"] == selected_company].sort_values("date").copy()
    if company_df.empty:
        return None
    group_avg = metrics_df.groupby("date", as_index=False)["delinquency_rate"].mean().rename(columns={"delinquency_rate": "value"})
    company_actual = company_df[["date", "delinquency_rate"]].rename(columns={"delinquency_rate": "value"})
    company_actual["series"] = selected_company
    group_avg["series"] = "그룹 평균"
    company_roll = company_df[["date", "delinquency_rate"]].copy()
    company_roll["value"] = company_roll["delinquency_rate"].rolling(3, min_periods=1).mean().round(2)
    company_roll = company_roll[["date", "value"]]
    company_roll["series"] = "3개월 이동평균"
    plot_df = pd.concat([company_actual, group_avg, company_roll], ignore_index=True)
    fig = px.line(
        plot_df,
        x="date",
        y="value",
        color="series",
        markers=True,
        color_discrete_map={selected_company: "#1d4ed8", "그룹 평균": "#94a3b8", "3개월 이동평균": "#dc2626"},
    )
    fig = apply_chart_theme(fig, height=340, margin=dict(l=0, r=0, t=16, b=0))
    fig.update_yaxes(title=None)
    fig.update_xaxes(title=None)
    return fig


def build_driver_mix_figure(selected_risk_row):
    driver_df = pd.DataFrame([
        {"항목": "신용리스크", "점수": float(selected_risk_row.get("credit_score", 0))},
        {"항목": "운영리스크", "점수": float(selected_risk_row.get("operational_score", 0))},
        {"항목": "민원/소비자보호", "점수": float(selected_risk_row.get("complaint_score", 0))},
        {"항목": "부동산집중", "점수": float(selected_risk_row.get("real_estate_score", 0))},
        {"항목": "SME집중", "점수": float(selected_risk_row.get("sme_score", 0))},
        {"항목": "추세압력", "점수": float(selected_risk_row.get("trend_pressure_score", 0))},
        {"항목": "이벤트로그", "점수": float(selected_risk_row.get("log_risk_score", 0))},
    ]).sort_values("점수", ascending=True)
    fig = px.bar(driver_df, x="점수", y="항목", orientation="h", color="점수", color_continuous_scale=["#dbeafe", "#93c5fd", "#2563eb"])
    fig = apply_chart_theme(fig, height=340, margin=dict(l=0, r=0, t=16, b=0), coloraxis_showscale=False)
    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None)
    return fig


def build_alert_distribution_figure(alerts):
    if alerts is None or alerts.empty:
        return None
    dist = alerts["severity"].value_counts().rename_axis("severity").reset_index(name="count")
    fig = px.pie(dist, names="severity", values="count", hole=0.56, color="severity", color_discrete_map={"High": "#dc2626", "Medium": "#f59e0b", "Low": "#059669"})
    return apply_chart_theme(fig, height=300, margin=dict(l=0, r=0, t=10, b=10))


def build_company_positioning_figure(risk_df):
    if risk_df.empty:
        return None
    fig = px.scatter(
        risk_df,
        x="latest_delinquency_rate",
        y="delinquency_change_pp",
        size="risk_score",
        color="risk_level",
        hover_name="company_name",
        text="company_name",
        color_discrete_map={"High": "#dc2626", "Medium": "#f59e0b", "Low": "#059669"},
    )
    fig.update_traces(textposition="top center")
    fig = apply_chart_theme(fig, height=360, margin=dict(l=0, r=0, t=16, b=0))
    fig.update_xaxes(title="현재 연체율")
    fig.update_yaxes(title="전월 대비 변화(%p)")
    return fig


def build_segment_delta_figure(segment_table):
    if segment_table.empty:
        return None
    plot_df = segment_table.sort_values("연체율 변화(%p)", ascending=True).copy()
    plot_df["상태"] = plot_df["연체율 변화(%p)"].apply(lambda x: "개선" if x < 0 else "악화")
    fig = px.bar(
        plot_df,
        x="연체율 변화(%p)",
        y="세그먼트",
        orientation="h",
        color="상태",
        text="연체율 변화(%p)",
        color_discrete_map={"악화": "#dc2626", "개선": "#059669"},
    )
    fig = apply_chart_theme(fig, height=380, margin=dict(l=0, r=0, t=16, b=0))
    fig.update_xaxes(title=None)
    fig.update_yaxes(title=None)
    return fig


def build_segment_positioning_figure(segment_table):
    if segment_table.empty:
        return None
    fig = px.scatter(
        segment_table,
        x="현재 잔액",
        y="연체율 변화(%p)",
        size="현재 차주수",
        color="포트폴리오군",
        hover_name="세그먼트",
        text="세그먼트",
    )
    fig.update_traces(textposition="top center")
    fig = apply_chart_theme(fig, height=380, margin=dict(l=0, r=0, t=16, b=0))
    fig.update_xaxes(title="현재 잔액")
    fig.update_yaxes(title="연체율 변화(%p)")
    return fig

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
if "focus_mode" not in st.session_state:
    st.session_state["focus_mode"] = "경영진 보고"
if "demo_mode" not in st.session_state:
    st.session_state["demo_mode"] = FOCUS_MODE_TO_DEMO.get(st.session_state["focus_mode"], "전체 흐름")
if "llm_cache_demo_mode" not in st.session_state:
    st.session_state["llm_cache_demo_mode"] = True

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

    llm_cache_demo_mode = st.toggle(
        "발표용 AI 데모 모드",
        value=st.session_state.get("llm_cache_demo_mode", True),
        help="API 키가 없거나 응답이 느린 환경에서도 사전 생성한 AI 응답을 즉시 시연합니다.",
    )
    st.session_state["llm_cache_demo_mode"] = llm_cache_demo_mode

    st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
    st.markdown("**현재 관제 기준**")
    st.markdown(
        f'<div class="sidebar-kpi"><b>기준 월</b> · {latest_month}<br><b>메인 포트폴리오</b> · {selected_company}<br><b>관제 초점</b> · {focus_mode}<br><b>경보 필터</b> · {", ".join(severity_filter) if severity_filter else "없음"}<br><b>AI 응답 모드</b> · {"Demo Cache" if llm_cache_demo_mode else ("Live LLM" if api_key_configured else "Rule-based Fallback")}</div>',
        unsafe_allow_html=True,
    )

    with st.expander("시연 흐름 가이드", expanded=False):
        st.markdown(
            """
            1. 주요 점검 계열사를 선택합니다.  
            2. 경영진 요약에서 Orchestrator 브리프를 확인합니다.
            3. 포트폴리오 세부진단에서 시나리오 값을 조정하고 해석을 확인합니다.  
            4. 대응계획 · 보고서 · Q&A에서 보고서와 임원 질의응답을 시연합니다.
            """
        )

    with st.expander("질의응답 · 보고서 도구", expanded=False):
        demo_question = st.selectbox(
            "질문 선택",
            _get_focus_question_options(selected_company, focus_mode),
        )
        if st.button("Q&A 실행", use_container_width=True):
            st.session_state["pending_qa_question"] = demo_question
        if st.button("원인 분석 보고서 갱신", use_container_width=True):
            st.session_state["pending_reason_refresh"] = True

    if llm_cache_demo_mode:
        st.caption("발표용 AI 데모 모드가 켜져 있어 사전 생성한 고품질 응답 캐시를 우선 사용합니다.")
    elif not api_key_configured:
        st.caption("생성형 브리핑 엔진이 연결되지 않으면 보고서와 질의응답은 자동으로 기본 분석 모드로 이어집니다.")

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

action_item_display = action_item_df.copy()
if "담당 영역" not in action_item_display.columns:
    if "소관 Agent" in action_item_display.columns:
        action_item_display["담당 영역"] = action_item_display["소관 Agent"]
    elif "담당 Agent" in action_item_display.columns:
        action_item_display["담당 영역"] = action_item_display["담당 Agent"]
if "목적" not in action_item_display.columns and "기대 효과" in action_item_display.columns:
    action_item_display["목적"] = action_item_display["기대 효과"]
action_item_display = action_item_display[[col for col in ["시점", "담당 영역", "액션 아이템", "목적"] if col in action_item_display.columns]].copy()
action_item_display = ensure_dataframe_columns(action_item_display, {"시점": "오늘", "담당 영역": "리스크관리", "액션 아이템": "기본 점검", "목적": "안정화"})

ranking_table = risk_df[["company_name", "risk_score", "risk_level", "latest_delinquency_rate", "delinquency_change_pp"]].rename(
    columns={
        "company_name": "계열사",
        "risk_score": "리스크 점수",
        "risk_level": "위험 단계",
        "latest_delinquency_rate": "현재 연체율",
        "delinquency_change_pp": "전월 대비 변화(%p)",
    }
).sort_values(["리스크 점수", "전월 대비 변화(%p)"], ascending=[False, False])

selected_company_alerts = filtered_alerts[filtered_alerts["company_name"] == selected_company].head(6).copy() if not filtered_alerts.empty else pd.DataFrame()
latest_driver_date = drivers_df["date"].dropna().max() if "date" in drivers_df.columns and not drivers_df.empty else pd.NaT
selected_driver_rows = drivers_df[(drivers_df["company_name"] == selected_company) & (drivers_df["date"] == latest_driver_date)].copy() if pd.notna(latest_driver_date) else pd.DataFrame()
if not selected_driver_rows.empty:
    selected_driver_rows["abs_bps"] = pd.to_numeric(selected_driver_rows["contribution_bps"], errors="coerce").abs().fillna(0)
    selected_driver_rows = selected_driver_rows.sort_values("abs_bps", ascending=False)

segment_table_display = segment_table.copy()
if not segment_table_display.empty:
    segment_table_display["위험도"] = segment_table_display["연체율 변화(%p)"].apply(lambda x: "High" if x >= 0.30 else "Medium" if x >= 0.10 else "Low")
    segment_table_display["점검 필요"] = segment_table_display["연체율 변화(%p)"].apply(lambda x: "즉시" if x >= 0.30 else "관찰" if x >= 0.10 else "안정")
    segment_table_display = segment_table_display[["세그먼트", "현재 연체율", "연체율 변화(%p)", "위험도", "점검 필요"]].head(7)

focus_view = _get_focus_view(
    focus_mode,
    filtered_alerts,
    selected_driver_rows,
    segment_table,
    action_item_display,
    ranking_table,
)
filtered_alerts = focus_view["alerts"]
top_signal_rows = focus_view["top_signals"]
action_item_display = focus_view["actions"] if not focus_view["actions"].empty else action_item_display
quick_actions = focus_view["quick_actions"] if not focus_view["quick_actions"].empty else action_item_display.head(3).copy()
segment_table = focus_view["segment_table"] if not focus_view["segment_table"].empty else segment_table
segment_table_display = focus_view["segment_table_display"] if not focus_view["segment_table_display"].empty else segment_table_display
ranking_table = focus_view["ranking_table"] if not focus_view["ranking_table"].empty else ranking_table
focus_card = focus_view["focus_card"]
focus_banner_message = focus_view["banner_message"]
focus_stress_defaults = focus_view["stress_defaults"]
focus_tab_labels = focus_view["tab_labels"]

selected_tone = "green" if selected_snapshot["mom_change_pp"] < 0 else "red" if selected_snapshot["mom_change_pp"] > 0 else "navy"

llm_context = build_llm_context(
    latest_month=latest_month,
    selected_company=selected_company,
    selected_snapshot=selected_snapshot,
    portfolio_summary=portfolio_summary,
    selected_risk_row=selected_risk_row,
    filtered_alerts=filtered_alerts,
    action_item_display=action_item_display,
    segment_table_display=segment_table_display,
    comparison_data={
        "best_company": comparison_data.get("best_company", "N/A"),
        "best_summary": comparison_data.get("best_summary", ""),
        "worst_company": comparison_data.get("worst_company", "N/A"),
        "worst_summary": comparison_data.get("worst_summary", ""),
    },
    focus_mode=focus_mode,
)

llm_context_signature = "|".join([
    latest_month,
    selected_company,
    focus_mode,
    f"{selected_snapshot['current_rate']:.2f}",
    f"{selected_snapshot['mom_change_pp']:.2f}",
    f"{selected_snapshot['vs_3m_avg_pp']:.2f}",
])
if st.session_state.get("llm_context_signature") != llm_context_signature:
    st.session_state["llm_context_signature"] = llm_context_signature
    with st.spinner("Agent들이 최신 리스크 컨텍스트를 재분석하고 있습니다..."):
        st.session_state["orchestrator_brief"] = safe_generate_orchestrator_brief(llm_context)
        st.session_state["pf_agent_note"] = safe_generate_specialist_note(
            "PF Surveillance Agent",
            "PF 브릿지론, 본PF, 차환 부담과 세그먼트 악화 징후 분석",
            llm_context,
        )
        st.session_state["collateral_agent_note"] = safe_generate_specialist_note(
            "Collateral & Recovery Agent",
            "담보 재평가, 회수 우선순위, 방어력 저하 구간 분석",
            llm_context,
        )
        st.session_state["early_warning_note"] = safe_generate_specialist_note(
            "Early Warning Agent",
            "조기경보, 최근 이벤트 로그, 민원 및 이상징후 변화 해석",
            llm_context,
        )
        st.session_state["qa_answer"] = safe_answer_question(
            f"왜 {selected_company}이 최우선 점검 대상인가",
            risk_df,
            alerts_df,
            metrics_df,
            llm_context=llm_context,
        )
    generated_at = _generation_label()
    st.session_state["orchestrator_brief_generated_at"] = generated_at
    st.session_state["pf_agent_note_generated_at"] = generated_at
    st.session_state["collateral_agent_note_generated_at"] = generated_at
    st.session_state["early_warning_note_generated_at"] = generated_at
    st.session_state["qa_answer_generated_at"] = generated_at

pending_question = st.session_state.pop("pending_qa_question", None)
if pending_question:
    with st.spinner("Q&A Agent가 답변을 생성하고 있습니다..."):
        st.session_state["qa_answer"] = safe_answer_question(
            pending_question,
            risk_df,
            alerts_df,
            metrics_df,
            llm_context=llm_context,
        )
    st.session_state["qa_answer_generated_at"] = _generation_label()

if st.session_state.pop("pending_reason_refresh", False):
    with st.spinner("Executive Reporting Agent가 보고서를 갱신하고 있습니다..."):
        st.session_state["reason_report"] = safe_generate_reason_report(
            metrics_df,
            drivers_df,
            segment_df,
            selected_company,
            llm_context=llm_context,
        )
    st.session_state["reason_report_company"] = selected_company
    st.session_state["reason_report_generated_at"] = _generation_label()


st.markdown(
    f"""
    <div class="hero-wrap">
        <div class="hero-kicker">JB CORPORATE FINANCE CRO MONITORING</div>
        <div class="hero-title">{selected_company} 기업금융 리스크 관제</div>
        <div class="hero-subtitle">
            경영진이 한 화면에서 <b>문제 징후 → 핵심 원인 → 즉시 조치</b>를 읽을 수 있도록 상단 브리프, 조기경보, 포트폴리오 진단,
            대응계획 흐름으로 재정렬했습니다. 복잡한 기능보다 <b>위험 우선순위와 실행 판단</b>이 먼저 보이도록 화면을 개편했습니다.
        </div>
        <div class="hero-subtitle"><b>AI Agents</b>가 조기경보, 포트폴리오 진단, 시나리오 해석, 보고서 생성을 역할별로 분담합니다.</div>
        <div class="info-chip-row">
            <div class="info-chip">기준 월 · {latest_month}</div>
            <div class="info-chip">기준 회사 · {selected_company}</div>
            <div class="info-chip">우선 관리 대상 · {max_score_company['company_name']}</div>
            <div class="info-chip">즉시 점검 필요 경보 · {high_alert_count}건</div>
            <div class="info-chip">PF 비중 · {portfolio_summary['pf_share']}%</div>
            <div class="info-chip">담보 기반 익스포저 · {portfolio_summary['secured_share']}%</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("배포 상태 / 헬스체크", expanded=False):
    render_deploy_status_banner(metrics_df, risk_df, alerts_df, latest_month)
    render_healthcheck_summary(metrics_df, logs_df, drivers_df, segment_df, risk_df, alerts_df)

st.markdown(
    f"""
    <div class="demo-banner">
        <b>현재 점검 시나리오 · {st.session_state['demo_mode']}</b><br>
        {DEMO_MODES.get(st.session_state['demo_mode'], DEMO_MODES['전체 흐름'])}<br>
        <span style="opacity:0.92;">{focus_banner_message}</span>
    </div>
    """,
    unsafe_allow_html=True,
)


row1 = st.columns(4)
with row1[0]:
    metric_card("최우선 계열사", max_score_company["company_name"], "그룹 기준 가장 먼저 봐야 할 계열사", "Watchlist")
with row1[1]:
    metric_card(focus_card["label"], focus_card["value"], focus_card["caption"], focus_card["badge"])
with row1[2]:
    metric_card("선택 계열사 연체율", f"{selected_snapshot['current_rate']:.2f}%", selected_snapshot["headline"], "Core KPI")
with row1[3]:
    metric_card("3M 평균 대비", f"{selected_snapshot['vs_3m_avg_pp']:+.2f}%p", f"전월 대비 {selected_snapshot['mom_change_pp']:+.2f}%p", "Trend")

FOCUS_TAB_GUIDE = {
    "그룹 스캔":     ("2. 조기경보 · 계열 비교",   "그룹 전체 경보 현황과 계열사 비교 순위를 확인합니다."),
    "PF 집중 점검":  ("3. 포트폴리오 세부진단",     "PF 브릿지론·본PF 세그먼트 악화 원인을 집중 점검합니다."),
    "기업대출 점검": ("3. 포트폴리오 세부진단",     "중소기업 운전자금·담보대출 세그먼트를 먼저 확인합니다."),
    "담보·회수 점검":("3. 포트폴리오 세부진단",     "담보 가치와 회수 우선순위 포지셔닝 차트를 점검합니다."),
    "경영진 보고":   ("1. 경영진 요약 → 4. 대응계획 · 보고서 · Q&A", "핵심 브리프 확인 후 보고서와 Q&A로 마무리합니다."),
}
tab_hint, tab_desc = FOCUS_TAB_GUIDE.get(focus_mode, ("1. 경영진 요약", ""))
st.markdown(
    f'<div class="demo-banner">📍 <b>관제 초점 · {focus_mode}</b> &nbsp;→&nbsp; <b>{tab_hint}</b> 탭을 먼저 확인하세요 &nbsp;|&nbsp; {tab_desc}</div>',
    unsafe_allow_html=True,
)

st.markdown("### 경영관리 화면")

tab1, tab2, tab3, tab4 = st.tabs(focus_tab_labels)


with tab1:
    brief_col, signal_col, action_col = st.columns([1.35, 1.0, 0.95])
    brief_body_html = f"""
    <div class="insight-metrics">
        <div class="insight-metric"><div class="insight-metric-label">현재 연체율</div><div class="insight-metric-value">{selected_snapshot['current_rate']:.2f}%</div></div>
        <div class="insight-metric"><div class="insight-metric-label">전월 대비</div><div class="insight-metric-value">{selected_snapshot['mom_change_pp']:+.2f}%p</div></div>
        <div class="insight-metric"><div class="insight-metric-label">3개월 평균 대비</div><div class="insight-metric-value">{selected_snapshot['vs_3m_avg_pp']:+.2f}%p</div></div>
    </div>
    <hr style="border:none;border-top:1px solid rgba(15,23,42,0.10);margin:14px 0 12px 0;">
    <div class="brief-headline">{selected_company}의 핵심 위험은 <b>{portfolio_summary['worst_segment']}</b> 중심의 연체 압력 확대입니다.</div>
    <div class="insight-note"><b>핵심 원인</b> · {selected_snapshot['negative_driver_summary']}</div>
    <div class="insight-note"><b>시사점</b> · {portfolio_summary['worst_segment']} 차환 일정, 담보 재평가, 회수 우선순위를 같은 회의 안건으로 묶어 점검해야 합니다.</div>
    """
    with brief_col:
        render_insight_panel(
            "당월 핵심 리스크 브리프",
            "이번 달 경영진이 가장 먼저 봐야 할 메시지",
            brief_body_html,
            tone=selected_tone,
        )
    with signal_col:
        st.markdown(f'<div class="small-title">{selected_company} 이상징후</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">숫자보다 먼저 봐야 할 이상 신호 3개를 압축했습니다.</div>', unsafe_allow_html=True)
        if top_signal_rows.empty:
            render_signal_card("핵심 위험 신호", selected_snapshot["negative_driver_summary"], f"{selected_snapshot['mom_change_pp']:+.2f}%p", "high")
        else:
            for _, row in top_signal_rows.iterrows():
                tone = "positive" if str(row.get("direction", "negative")) == "positive" else "high"
                render_signal_card(row["driver_name"], row["description"], f"{float(row['contribution_bps']):+.0f}bp", tone)
    with action_col:
        st.markdown('<div class="small-title">즉시 점검 과제</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">오늘부터 이번 달까지 실제로 움직여야 할 과제입니다.</div>', unsafe_allow_html=True)
        for _, row in quick_actions.iterrows():
            render_action_card(row["시점"], row["액션 아이템"], row["목적"])

    trend_col, driver_col = st.columns([1.15, 0.85])
    with trend_col:
        st.markdown('<div class="small-title">최근 6개월 위험 추세</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="section-subtitle">{selected_company} 추세, 그룹 평균, 3개월 이동평균을 한 화면에서 비교합니다.</div>', unsafe_allow_html=True)
        company_trend_fig = build_company_trend_figure(metrics_df, selected_company)
        if company_trend_fig is None:
            st.info("추세 차트를 그릴 데이터가 없습니다.")
        else:
            st.plotly_chart(company_trend_fig, use_container_width=True)
    with driver_col:
        st.markdown('<div class="small-title">위험 요인 구성</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">현재 점수를 끌어올리는 요인을 항목별로 분해했습니다.</div>', unsafe_allow_html=True)
        st.plotly_chart(build_driver_mix_figure(selected_risk_row), use_container_width=True)

    top_action = quick_actions.iloc[0]["액션 아이템"] if not quick_actions.empty else "차주 리스트 재점검"
    top_purpose = quick_actions.iloc[0]["목적"] if not quick_actions.empty else "취약 차주군 우선 점검"
    st.markdown('<div class="decision-strip">', unsafe_allow_html=True)
    st.markdown('<div class="small-title">경영 판단 포인트</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <ul>
            <li><b>{selected_company}</b>의 현재 위험 중심은 <b>{portfolio_summary['worst_segment']}</b>이며, 현재 연체율은 <b>{selected_snapshot['current_rate']:.2f}%</b>입니다.</li>
            <li>최대 익스포저는 <b>{portfolio_summary['largest_balance_segment']}</b>이고, 우선 실행 과제는 <b>{top_action}</b>입니다.</li>
            <li>즉시 점검 필요 경보는 <b>{high_alert_count}건</b>이며, 이번 라운드의 핵심 목적은 <b>{top_purpose}</b>입니다.</li>
        </ul>
        """,
        unsafe_allow_html=True,
    )


with tab2:
    top_left, top_right = st.columns([1.2, 0.8])
    with top_left:
        st.markdown('<div class="small-title">당월 조기경보 현황</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">실제로 점검해야 할 경보만 카드형으로 압축했습니다.</div>', unsafe_allow_html=True)
        if filtered_alerts.empty:
            st.info("표시할 경보가 없습니다.")
        else:
            for _, row in filtered_alerts.head(6).iterrows():
                render_alert_card(row)
        st.caption(f"현재 관제 초점({focus_mode}) 기준으로 재구성된 경보 목록입니다.")
    with top_right:
        st.markdown('<div class="small-title">경보 분포</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">High, Medium, Low 구성으로 현재 긴급도를 파악합니다.</div>', unsafe_allow_html=True)
        alert_dist_fig = build_alert_distribution_figure(filtered_alerts if not filtered_alerts.empty else alerts_df)
        if alert_dist_fig is None:
            st.info("경보 분포를 계산할 데이터가 없습니다.")
        else:
            st.plotly_chart(alert_dist_fig, use_container_width=True)

    mid_left, mid_right = st.columns([0.95, 1.05])
    with mid_left:
        st.markdown('<div class="small-title">계열사 건전성 비교</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">랭킹 표는 핵심 컬럼만 남겨 빠르게 읽히도록 정리했습니다.</div>', unsafe_allow_html=True)
        st.dataframe(ranking_table.head(4), use_container_width=True, hide_index=True)
    with mid_right:
        st.markdown('<div class="small-title">리스크 포지셔닝</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">현재 연체율과 전월 대비 변화를 동시에 보면 어디가 위험한지 더 빨리 보입니다.</div>', unsafe_allow_html=True)
        position_fig = build_company_positioning_figure(risk_df)
        if position_fig is None:
            st.info("포지셔닝 차트를 생성할 데이터가 없습니다.")
        else:
            st.plotly_chart(position_fig, use_container_width=True)

    bottom_left, bottom_right = st.columns([1.2, 0.8])
    with bottom_left:
        st.markdown('<div class="small-title">핵심 지표 추이 비교</div>', unsafe_allow_html=True)
        _metric_options = ["delinquency_rate", "complaints", "abnormal_events", "exposure_real_estate", "exposure_sme"]
        _default_metric = FOCUS_DEFAULT_METRIC.get(focus_mode, "delinquency_rate")
        metric_choice = st.selectbox("추이 지표 선택", _metric_options, index=_metric_options.index(_default_metric))
        metric_label_map = {
            "delinquency_rate": "연체율",
            "complaints": "민원 건수",
            "abnormal_events": "이상 이벤트 수",
            "exposure_real_estate": "부동산 익스포저",
            "exposure_sme": "SME 익스포저",
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
                color_discrete_sequence=["#1d4ed8", "#0f766e", "#9333ea", "#dc2626"],
            )
            trend_fig = apply_chart_theme(trend_fig, height=360, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(trend_fig, use_container_width=True)
    with bottom_right:
        st.markdown('<div class="small-title">해석 포인트</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">차트를 본 뒤 바로 말할 수 있어야 하는 문장만 남겼습니다.</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            - <b>{selected_company}</b>는 현재 선택 지표 기준으로 최근 구간의 변동성이 가장 큰 축에 포함됩니다.  
            - <b>{comparison_data['best_company']}</b>는 개선 벤치마크로 활용할 수 있고, <b>{comparison_data['worst_company']}</b>는 우선 관리 대상으로 봐야 합니다.  
            - 계열 비교 시 <b>현재 수준</b>보다 <b>전월 변화와 평균 대비 이탈</b>을 함께 보는 것이 실무적으로 더 유효합니다.
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="small-title">리스크 축 히트맵</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">계열사별 어떤 위험 축이 점수를 끌어올리는지 한 번에 비교합니다.</div>', unsafe_allow_html=True)
    heatmap_fig = build_risk_heatmap_figure(risk_df)
    if heatmap_fig is None:
        st.info("리스크 히트맵을 생성할 데이터가 없습니다.")
    else:
        st.plotly_chart(heatmap_fig, use_container_width=True)


with tab3:
    top_metrics = st.columns(3)
    with top_metrics[0]:
        metric_card("PF/프로젝트금융 비중", f"{portfolio_summary['pf_share']:.1f}%", "브릿지론 중심 익스포저 집중 수준", "PF")
    with top_metrics[1]:
        metric_card("담보 기반 익스포저 비중", f"{portfolio_summary['secured_share']:.1f}%", "담보 재평가·회수정책 영향이 큰 구조", "Collateral")
    with top_metrics[2]:
        metric_card("최대 익스포저 세그먼트", portfolio_summary['largest_balance_segment'], f"현재 잔액 {portfolio_summary['largest_balance']:.1f}", "Exposure")

    st.markdown('<div class="small-title">세그먼트 위험 히트맵</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">세그먼트별 위험이 어디에 몰려 있는지 숫자보다 먼저 보이게 배치했습니다.</div>', unsafe_allow_html=True)
    segment_heatmap_fig = build_segment_heatmap_figure(segment_table)
    if segment_heatmap_fig is None:
        st.info("세그먼트 히트맵을 생성할 데이터가 없습니다.")
    else:
        st.plotly_chart(segment_heatmap_fig, use_container_width=True)

    mid_left, mid_right = st.columns([1, 1])
    with mid_left:
        st.markdown('<div class="small-title">세그먼트별 연체율 변화</div>', unsafe_allow_html=True)
        seg_fig = build_segment_delta_figure(segment_table)
        if seg_fig is None:
            st.info("세그먼트 변화 데이터가 없습니다.")
        else:
            st.plotly_chart(seg_fig, use_container_width=True)
    with mid_right:
        st.markdown('<div class="small-title">잔액 대비 위험 포지셔닝</div>', unsafe_allow_html=True)
        pos_fig = build_segment_positioning_figure(segment_table)
        if pos_fig is None:
            st.info("리스크 포지셔닝 산포도에 사용할 데이터가 없습니다.")
        else:
            st.plotly_chart(pos_fig, use_container_width=True)

    detail_left, detail_right = st.columns([1.05, 0.95])
    with detail_left:
        st.markdown(f'<div class="small-title">{selected_company} 포트폴리오 구조 요약</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="premium-note">PF 비중 <b>{portfolio_summary["pf_share"]}%</b> · 담보 기반 비중 <b>{portfolio_summary["secured_share"]}%</b><br>'
            f'최대 익스포저는 <b>{portfolio_summary["largest_balance_segment"]}</b>, 집중 관리 세그먼트는 <b>{portfolio_summary["worst_segment"]}</b>입니다.<br>'
            f'개선 신호는 <b>{portfolio_summary["best_segment"]}</b>에서 확인됩니다.</div>',
            unsafe_allow_html=True,
        )
        render_reason_box("연체율 상승/악화 이유", selected_snapshot["negative_driver_summary"], positive=False)
        render_reason_box("개선 신호", selected_snapshot["positive_driver_summary"], positive=True)
    with detail_right:
        st.markdown('<div class="small-title">세그먼트 상세 점검</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">표는 상위 7개만 남겨 읽기 부담을 줄였습니다.</div>', unsafe_allow_html=True)
        st.dataframe(segment_table_display, use_container_width=True, hide_index=True)

    st.markdown('<div class="small-title">스트레스 시나리오 점검</div>', unsafe_allow_html=True)
    stress_left, stress_right = st.columns([0.9, 1.1])
    with stress_left:
        st.markdown('<div class="section-subtitle">스트레스 가정</div>', unsafe_allow_html=True)
        pf_stress = st.slider("PF 차환 부담(%p)", min_value=0.0, max_value=1.2, value=float(focus_stress_defaults["pf"]), step=0.05)
        collateral_stress = st.slider("담보 회수율 저하(%p)", min_value=0.0, max_value=1.0, value=float(focus_stress_defaults["collateral"]), step=0.05)
        sme_stress = st.slider("SME 업황 악화(%p)", min_value=0.0, max_value=1.0, value=float(focus_stress_defaults["sme"]), step=0.05)
    scenario_result = safe_simulate_what_if(selected_company, risk_df, segment_df, pf_stress, collateral_stress, sme_stress)
    with stress_right:
        st.markdown('<div class="section-subtitle">영향 추정</div>', unsafe_allow_html=True)
        scenario_metrics = st.columns(4)
        with scenario_metrics[0]:
            metric_card("현재 연체율", f"{scenario_result['base_rate']:.2f}%", "기준 시점", "Base")
        with scenario_metrics[1]:
            metric_card("예상 연체율", f"{scenario_result['projected_rate']:.2f}%", "스트레스 반영 후", "Scenario")
        with scenario_metrics[2]:
            metric_card("추가 충격", f"{scenario_result['stress_delta']:+.2f}%p", scenario_result["impact_summary"], "Shock")
        with scenario_metrics[3]:
            metric_card("예상 리스크 레벨", scenario_result["projected_risk_level"], f"예상 점수 {scenario_result['projected_risk_score']}", "Risk")
    scenario_df = pd.DataFrame({"구분": ["기준 연체율", "예상 연체율"], "연체율": [scenario_result["base_rate"], scenario_result["projected_rate"]]})
    scenario_fig = px.bar(scenario_df, x="구분", y="연체율", color="구분", text="연체율", color_discrete_sequence=["#94a3b8", "#dc2626"])
    scenario_fig = apply_chart_theme(scenario_fig, height=300, margin=dict(l=0, r=0, t=16, b=0), showlegend=False)
    st.plotly_chart(scenario_fig, use_container_width=True)
    st.markdown(
        f"""
        <div class="decision-strip">
            <div class="small-title">영향 요약</div>
            <ul>
                <li>가장 민감한 충격 조합은 PF 차환 부담과 담보 회수율 저하입니다.</li>
                <li>현재 구조에서는 <b>{portfolio_summary['worst_segment']}</b>가 스트레스 확대 시 가장 먼저 추가 점검 대상이 됩니다.</li>
                <li>실무 대응은 차주 리스트 재점검 → 담보 재평가 → 회수정책 조정 순으로 가져가는 것이 자연스럽습니다.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    scenario_signature = f"{llm_context_signature}|{pf_stress:.2f}|{collateral_stress:.2f}|{sme_stress:.2f}"
    if st.session_state.get("scenario_signature") != scenario_signature:
        st.session_state["scenario_signature"] = scenario_signature
        with st.spinner("Scenario Interpretation Agent가 해석을 생성하고 있습니다..."):
            st.session_state["scenario_agent_note"] = safe_interpret_scenario(llm_context, scenario_result)
        st.session_state["scenario_agent_generated_at"] = _generation_label()

    st.markdown('<div class="small-title">Scenario Interpretation Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">스트레스 결과를 실무 점검 순서와 보고 포인트 중심으로 자동 정리합니다.</div>', unsafe_allow_html=True)
    scenario_note = st.session_state.get("scenario_agent_note", safe_interpret_scenario(llm_context, scenario_result))
    st.markdown(str(scenario_note).replace("\n", "  \n"))
    st.caption(f"생성 시각 · {st.session_state.get('scenario_agent_generated_at', '-')}")


with tab4:
    st.markdown('<div class="small-title">단기 대응 로드맵</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">보고용 표가 아니라 실제 실행 일정처럼 읽히도록 정리했습니다.</div>', unsafe_allow_html=True)
    st.dataframe(action_item_display.head(5), use_container_width=True, hide_index=True)
    st.caption(f"현재 관제 초점({focus_mode})에 맞게 재정렬한 실행 과제입니다.")

    with st.expander("관리자 전용 · Agent 실행 흔적", expanded=False):
        st.markdown('<div class="section-subtitle">에이전트별 입력, 판단, 출력을 관리자만 필요 시 확인할 수 있게 숨겼습니다.</div>', unsafe_allow_html=True)
        st.dataframe(agent_trace_df.head(8), use_container_width=True, hide_index=True)

    doc_left, doc_right = st.columns([1, 1])
    with doc_left:
        st.markdown('<div class="doc-card report-box">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">Executive Reporting Agent · 선택 계열사 보고서</div>', unsafe_allow_html=True)
        st.markdown('<ul class="doc-list"><li>핵심 위험 요약</li><li>포트폴리오 구조</li><li>대응 일정 및 담당</li></ul>', unsafe_allow_html=True)
        if "reason_report" not in st.session_state or st.session_state.get("reason_report_signature") != llm_context_signature:
            with st.spinner("Executive Reporting Agent가 선택 계열사 보고서를 준비하고 있습니다..."):
                st.session_state["reason_report"] = safe_generate_reason_report(metrics_df, drivers_df, segment_df, selected_company, llm_context=llm_context)
            st.session_state["reason_report_company"] = selected_company
            st.session_state["reason_report_signature"] = llm_context_signature
            st.session_state["reason_report_generated_at"] = _generation_label()
        st.text_area("회사별 보고서 미리보기", st.session_state["reason_report"], height=320)
        st.caption(f"생성 시각 · {st.session_state.get('reason_report_generated_at', '-')}")
        company_pdf = build_company_report_pdf(selected_company, latest_month, selected_snapshot, portfolio_summary, st.session_state["reason_report"], action_item_display)
        st.download_button("PDF 다운로드", data=company_pdf, file_name=f"{selected_company}_{latest_month}_company_report.pdf", mime="application/pdf", use_container_width=True)
    with doc_right:
        st.markdown('<div class="doc-card report-box">', unsafe_allow_html=True)
        st.markdown('<div class="small-title">Orchestrator Agent · 그룹 브리프</div>', unsafe_allow_html=True)
        st.markdown('<ul class="doc-list"><li>계열사 비교</li><li>주요 경보</li><li>경영 판단 포인트</li></ul>', unsafe_allow_html=True)
        if "executive_report" not in st.session_state or st.session_state.get("executive_report_signature") != llm_context_signature:
            with st.spinner("Orchestrator Agent가 그룹 브리프를 정리하고 있습니다..."):
                st.session_state["executive_report"] = safe_generate_executive_report(risk_df, alerts_df, latest_month, llm_context=llm_context)
            st.session_state["executive_report_signature"] = llm_context_signature
            st.session_state["executive_report_generated_at"] = _generation_label()
        st.text_area("그룹 브리프 미리보기", st.session_state["executive_report"], height=320)
        st.caption(f"생성 시각 · {st.session_state.get('executive_report_generated_at', '-')}")
        group_pdf = build_group_brief_pdf(latest_month, st.session_state["executive_report"], comparison_data["trend_table"], filtered_alerts if not filtered_alerts.empty else alerts_df)
        st.download_button("PDF 다운로드 ", data=group_pdf, file_name=f"group_brief_{latest_month}.pdf", mime="application/pdf", use_container_width=True)

    qa_left, qa_right = st.columns([0.8, 1.2])
    with qa_left:
        st.markdown('<div class="small-title">임원 예상 질의 대응</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">자주 나오는 질문과 자유 질문을 모두 바로 시연할 수 있게 구성했습니다.</div>', unsafe_allow_html=True)
        focus_questions = _get_focus_question_options(selected_company, focus_mode)
        faq_items = [(question, question) for question in focus_questions]
        faq_items.append(("스트레스 확대 시 가장 먼저 흔들리는 세그먼트는 무엇인가", "스트레스 확대 시 가장 먼저 흔들리는 세그먼트는 무엇인가"))
        for idx, (label, query) in enumerate(faq_items, start=1):
            if st.button(label, key=f"faq_{idx}", use_container_width=True):
                with st.spinner("Q&A Agent가 답변을 생성하고 있습니다..."):
                    st.session_state["qa_answer"] = safe_answer_question(query, risk_df, alerts_df, metrics_df, llm_context=llm_context)
                st.session_state["qa_answer_generated_at"] = _generation_label()
        custom_q = st.text_input("직접 질문 입력", placeholder="예: 이번 달 가장 먼저 점검해야 할 세그먼트는 무엇인가")
        if st.button("질문하기", use_container_width=True) and custom_q:
            with st.spinner("Q&A Agent가 답변을 생성하고 있습니다..."):
                st.session_state["qa_answer"] = safe_answer_question(custom_q, risk_df, alerts_df, metrics_df, llm_context=llm_context)
            st.session_state["qa_answer_generated_at"] = _generation_label()
        st.markdown('</div>', unsafe_allow_html=True)
    with qa_right:
        st.markdown('<div class="small-title">답변 및 근거</div>', unsafe_allow_html=True)
        answer_text = st.session_state.get("qa_answer", safe_answer_question(f"왜 {selected_company}이 최우선 점검 대상인가", risk_df, alerts_df, metrics_df, llm_context=llm_context))
        st.markdown("> " + str(answer_text).replace("\n", "\n> "))
        st.caption(f"생성 시각 · {st.session_state.get('qa_answer_generated_at', '-')}")
        st.markdown('#### 현재 선택 계열사 핵심 요인')
        driver_items = [item.strip() for item in str(selected_risk_row.get("top_drivers", "")).split("|") if item.strip()]
        if driver_items:
            for item in driver_items[:5]:
                st.markdown(f"- {item}")
        else:
            st.caption("표시할 핵심 요인이 없습니다.")


st.caption("상단 브리프, 조기경보 보드, 세그먼트 히트맵, 문서형 다운로드 영역 중심으로 화면을 재정렬했습니다.")
