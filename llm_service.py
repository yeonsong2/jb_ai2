import json
import os
from typing import Any

import streamlit as st

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None

DEFAULT_MODEL = "gpt-4o-mini"


def get_api_key() -> str | None:
    try:
        return st.secrets["OPENAI_API_KEY"]
    except Exception:
        return os.environ.get("OPENAI_API_KEY")


def get_openai_client():
    api_key = get_api_key()
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def _call_chat_model(system_prompt: str, user_payload: dict[str, Any], model: str = DEFAULT_MODEL, temperature: float = 0.3):
    client = get_openai_client()
    if client is None:
        return None, "OPENAI_API_KEY 또는 openai 패키지가 없어 LLM 기능을 실행할 수 없습니다."

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, indent=2)},
            ],
        )
        text = response.choices[0].message.content if response.choices else ""
        return text or "응답이 비어 있습니다.", None
    except Exception as exc:  # pragma: no cover
        return None, str(exc)


def build_llm_context(
    latest_month: str,
    selected_company: str,
    selected_snapshot: dict,
    portfolio_summary: dict,
    selected_risk_row,
    filtered_alerts,
    action_item_display,
    segment_table_display,
    comparison_data: dict,
    focus_mode: str,
):
    top_alerts = filtered_alerts.head(5).to_dict(orient="records") if hasattr(filtered_alerts, "head") else []
    top_actions = action_item_display.head(5).to_dict(orient="records") if hasattr(action_item_display, "head") else []
    top_segments = segment_table_display.head(7).to_dict(orient="records") if hasattr(segment_table_display, "head") else []

    risk_row = {}
    if hasattr(selected_risk_row, "to_dict"):
        risk_row = selected_risk_row.to_dict()

    return {
        "latest_month": latest_month,
        "selected_company": selected_company,
        "focus_mode": focus_mode,
        "snapshot": {
            "current_rate": selected_snapshot.get("current_rate", 0.0),
            "mom_change_pp": selected_snapshot.get("mom_change_pp", 0.0),
            "vs_3m_avg_pp": selected_snapshot.get("vs_3m_avg_pp", 0.0),
            "headline": selected_snapshot.get("headline", ""),
            "positive_driver_summary": selected_snapshot.get("positive_driver_summary", ""),
            "negative_driver_summary": selected_snapshot.get("negative_driver_summary", ""),
        },
        "portfolio_summary": {
            "pf_share": portfolio_summary.get("pf_share", 0.0),
            "secured_share": portfolio_summary.get("secured_share", 0.0),
            "worst_segment": portfolio_summary.get("worst_segment", "데이터 없음"),
            "worst_change_pp": portfolio_summary.get("worst_change_pp", 0.0),
            "best_segment": portfolio_summary.get("best_segment", "데이터 없음"),
            "best_change_pp": portfolio_summary.get("best_change_pp", 0.0),
            "largest_balance_segment": portfolio_summary.get("largest_balance_segment", "데이터 없음"),
            "largest_balance": portfolio_summary.get("largest_balance", 0.0),
        },
        "risk_row": {
            "risk_score": risk_row.get("risk_score", 0.0),
            "risk_level": risk_row.get("risk_level", "Low"),
            "top_drivers": risk_row.get("top_drivers", ""),
            "executive_headline": risk_row.get("executive_headline", ""),
            "credit_score": risk_row.get("credit_score", 0),
            "complaint_score": risk_row.get("complaint_score", 0),
            "operational_score": risk_row.get("operational_score", 0),
            "real_estate_score": risk_row.get("real_estate_score", 0),
            "sme_score": risk_row.get("sme_score", 0),
            "trend_pressure_score": risk_row.get("trend_pressure_score", 0),
            "log_risk_score": risk_row.get("log_risk_score", 0),
        },
        "alerts": top_alerts,
        "action_items": top_actions,
        "segments": top_segments,
        "comparison": comparison_data,
    }


def generate_orchestrator_brief(context: dict[str, Any], model: str = DEFAULT_MODEL):
    system_prompt = """
당신은 JB금융그룹 CRO 대시보드의 Orchestrator Agent다.
목표는 여러 분석 결과를 종합해 경영진이 20초 안에 읽는 브리프를 작성하는 것이다.
반드시 한국어로 작성하고, 데이터에 없는 내용은 추정하지 마라.
전체 출력은 8줄 이내로 제한하라.
출력 형식:
[핵심 리스크] 1~2문장
[주요 원인] bullet 2개 이내
[즉시 조치] bullet 2개 이내
[경영 판단 포인트] 1문장
숫자와 세그먼트명을 우선 사용하라.
""".strip()
    return _call_chat_model(system_prompt, context, model=model, temperature=0.2)


def generate_specialist_opinion(agent_name: str, focus: str, context: dict[str, Any], model: str = DEFAULT_MODEL):
    system_prompt = f"""
당신은 {agent_name}다.
전문 관점은 {focus}다.
주어진 데이터만 바탕으로 실무형 의견을 작성하라.
반드시 한국어로 작성하고, 4개 섹션으로 답하라.
[현재 판단]
[핵심 근거]
[우선 점검 항목]
[실무 메모]
각 섹션은 1문장, 전체는 6줄 이내로 제한하라.
중복 설명과 배경 서술은 제거하라.
""".strip()
    return _call_chat_model(system_prompt, context, model=model, temperature=0.25)


def generate_executive_report_with_llm(context: dict[str, Any], model: str = DEFAULT_MODEL):
    system_prompt = """
당신은 Executive Reporting Agent다.
경영진 보고서 초안을 한국어로 작성하라.
과장하지 말고 숫자와 시사점 중심으로 작성하라.
출력 형식:
1. 당월 요약
2. 핵심 위험 요인
3. 포트폴리오 구조 해석
4. 대응 우선순위
5. 경영진 한 줄 결론
각 항목은 1~2줄로 제한하고, 전체는 12줄 이내로 작성하라.
""".strip()
    return _call_chat_model(system_prompt, context, model=model, temperature=0.2)


def answer_exec_question_with_llm(question: str, context: dict[str, Any], model: str = DEFAULT_MODEL):
    payload = {"question": question, "context": context}
    system_prompt = """
당신은 임원 질의응답 Agent다.
질문에 대해 한국어로 3문장 이내로 답하라.
마지막에 '근거:'로 시작하는 한 줄에 핵심 수치 또는 판단 근거 2개만 정리하라.
데이터에 없는 내용은 만들지 마라.
""".strip()
    return _call_chat_model(system_prompt, payload, model=model, temperature=0.2)


def interpret_scenario_with_llm(context: dict[str, Any], scenario_result: dict[str, Any], model: str = DEFAULT_MODEL):
    payload = {"context": context, "scenario_result": scenario_result}
    system_prompt = """
당신은 Scenario Interpretation Agent다.
스트레스 시나리오 결과를 실무자가 바로 행동할 수 있도록 해석하라.
한국어로 다음 형식으로 작성하라.
[영향 해석]
[가장 민감한 포인트]
[우선 대응]
각 섹션은 1문장, 전체는 6줄 이내로 간결하게 작성하라.
""".strip()
    return _call_chat_model(system_prompt, payload, model=model, temperature=0.25)
