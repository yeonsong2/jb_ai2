import pandas as pd


SEVERITY_WEIGHTS = {"High": 18, "Medium": 10, "Low": 4}
TYPE_WEIGHTS = {
    "Bank": 1.0,
    "Capital": 1.08,
    "Overseas Bank": 0.95,
    "Asset Management": 0.9,
}


def _safe_pct_change(current, previous):
    if previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 1)


def _latest_and_previous(group: pd.DataFrame):
    latest = group.iloc[-1]
    previous = group.iloc[-2] if len(group) > 1 else latest
    return latest, previous


def _score_component(change_pct, strong_threshold, medium_threshold, high_score, medium_score):
    if change_pct >= strong_threshold:
        return high_score
    if change_pct >= medium_threshold:
        return medium_score
    return 0


def calculate_company_risk(metrics_df: pd.DataFrame, logs_df: pd.DataFrame | None = None) -> pd.DataFrame:
    metrics_df = metrics_df.sort_values(["company_name", "date"]).copy()
    rows = []

    latest_month = metrics_df["date"].max().to_period("M")
    recent_logs = pd.DataFrame()
    if logs_df is not None and not logs_df.empty:
        recent_logs = logs_df[logs_df["date"].dt.to_period("M") == latest_month].copy()

    for company, group in metrics_df.groupby("company_name"):
        latest, previous = _latest_and_previous(group)
        company_type = latest["company_type"]
        type_weight = TYPE_WEIGHTS.get(company_type, 1.0)

        delinquency_change_pct = _safe_pct_change(
            latest["delinquency_rate"], previous["delinquency_rate"]
        )
        complaints_change_pct = _safe_pct_change(latest["complaints"], previous["complaints"])
        abnormal_events_change_pct = _safe_pct_change(
            latest["abnormal_events"], previous["abnormal_events"]
        )
        real_estate_change_pct = _safe_pct_change(
            latest["exposure_real_estate"], previous["exposure_real_estate"]
        )
        sme_change_pct = _safe_pct_change(latest["exposure_sme"], previous["exposure_sme"])

        component_scores = {
            "신용리스크": _score_component(delinquency_change_pct, 20, 10, 34, 20),
            "민원/소비자보호": _score_component(complaints_change_pct, 18, 10, 18, 10),
            "운영리스크": _score_component(abnormal_events_change_pct, 20, 10, 22, 12),
            "부동산 집중": _score_component(real_estate_change_pct, 15, 8, 12, 7),
            "SME 집중": _score_component(sme_change_pct, 12, 6, 10, 5),
        }

        log_risk_score = 0
        log_messages = []
        if not recent_logs.empty:
            company_logs = recent_logs[recent_logs["company_name"] == company]
            for _, log_row in company_logs.iterrows():
                log_risk_score += SEVERITY_WEIGHTS.get(log_row["severity"], 0)
                log_messages.append(f"로그:{log_row['issue_type']}({log_row['severity']})")

        base_score = sum(component_scores.values())
        weighted_score = round(min((base_score + log_risk_score) * type_weight, 100), 1)

        if weighted_score >= 75:
            risk_level = "High"
        elif weighted_score >= 45:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        drivers = [name for name, score in component_scores.items() if score > 0]
        drivers.extend(log_messages)
        if not drivers:
            drivers = ["주요 이상 없음"]

        rows.append(
            {
                "company_name": company,
                "company_type": company_type,
                "risk_score": weighted_score,
                "risk_level": risk_level,
                "delinquency_change_pct": delinquency_change_pct,
                "complaints_change_pct": complaints_change_pct,
                "abnormal_events_change_pct": abnormal_events_change_pct,
                "real_estate_change_pct": real_estate_change_pct,
                "sme_change_pct": sme_change_pct,
                "latest_delinquency_rate": latest["delinquency_rate"],
                "latest_complaints": latest["complaints"],
                "latest_abnormal_events": latest["abnormal_events"],
                "latest_exposure_real_estate": latest["exposure_real_estate"],
                "latest_exposure_sme": latest["exposure_sme"],
                "credit_score": component_scores["신용리스크"],
                "complaint_score": component_scores["민원/소비자보호"],
                "operational_score": component_scores["운영리스크"],
                "real_estate_score": component_scores["부동산 집중"],
                "sme_score": component_scores["SME 집중"],
                "log_risk_score": log_risk_score,
                "top_drivers": "|".join(drivers[:5]),
                "top_drivers_text": ", ".join(drivers[:3]),
            }
        )

    return pd.DataFrame(rows).sort_values("risk_score", ascending=False).reset_index(drop=True)


def detect_alerts(metrics_df: pd.DataFrame, logs_df: pd.DataFrame) -> pd.DataFrame:
    metrics_df = metrics_df.sort_values(["company_name", "date"]).copy()
    alerts = []

    for company, group in metrics_df.groupby("company_name"):
        latest, previous = _latest_and_previous(group)

        delinquency_change_pct = _safe_pct_change(
            latest["delinquency_rate"], previous["delinquency_rate"]
        )
        complaints_change_pct = _safe_pct_change(latest["complaints"], previous["complaints"])
        abnormal_events_change_pct = _safe_pct_change(
            latest["abnormal_events"], previous["abnormal_events"]
        )
        real_estate_change_pct = _safe_pct_change(
            latest["exposure_real_estate"], previous["exposure_real_estate"]
        )
        sme_change_pct = _safe_pct_change(latest["exposure_sme"], previous["exposure_sme"])

        if delinquency_change_pct >= 20:
            alerts.append(
                {
                    "company_name": company,
                    "alert_type": "신용리스크 경보",
                    "severity": "High",
                    "detail": f"연체율이 전월 대비 {delinquency_change_pct}% 증가했습니다.",
                    "recommended_action": "연체 증가 차주군과 포트폴리오를 우선 점검하고 취약 섹터를 재분석하세요.",
                }
            )

        if complaints_change_pct >= 18:
            alerts.append(
                {
                    "company_name": company,
                    "alert_type": "민원 증가 경보",
                    "severity": "Medium",
                    "detail": f"민원 건수가 전월 대비 {complaints_change_pct}% 증가했습니다.",
                    "recommended_action": "민원 유형을 세분화하고 반복 발생 프로세스를 우선 개선하세요.",
                }
            )

        if abnormal_events_change_pct >= 20:
            alerts.append(
                {
                    "company_name": company,
                    "alert_type": "운영리스크 경보",
                    "severity": "High",
                    "detail": f"이상 이벤트 수가 전월 대비 {abnormal_events_change_pct}% 증가했습니다.",
                    "recommended_action": "이상 이벤트 발생 부서, 채널, 프로세스를 즉시 점검하세요.",
                }
            )

        if real_estate_change_pct >= 15:
            alerts.append(
                {
                    "company_name": company,
                    "alert_type": "부동산 익스포저 집중 경보",
                    "severity": "Medium",
                    "detail": f"부동산 익스포저가 전월 대비 {real_estate_change_pct}% 증가했습니다.",
                    "recommended_action": "업종 집중도와 내부 한도 운영 상태를 재검토하세요.",
                }
            )

        if sme_change_pct >= 12:
            alerts.append(
                {
                    "company_name": company,
                    "alert_type": "SME 익스포저 확대 경보",
                    "severity": "Medium",
                    "detail": f"중소기업 익스포저가 전월 대비 {sme_change_pct}% 증가했습니다.",
                    "recommended_action": "차주군별 건전성 변화를 점검하고 취약 업종 비중을 확인하세요.",
                }
            )

    latest_month = metrics_df["date"].max().to_period("M")
    recent_logs = logs_df[logs_df["date"].dt.to_period("M") == latest_month]
    for _, row in recent_logs.iterrows():
        alerts.append(
            {
                "company_name": row["company_name"],
                "alert_type": row["issue_type"],
                "severity": row["severity"],
                "detail": row["description"],
                "recommended_action": "세부 원인 로그를 검토하고 즉시 대응 계획을 수립하세요.",
            }
        )

    if not alerts:
        return pd.DataFrame(
            columns=["company_name", "alert_type", "severity", "detail", "recommended_action"]
        )

    severity_order = {"High": 2, "Medium": 1, "Low": 0}
    alert_df = pd.DataFrame(alerts)
    alert_df["severity_rank"] = alert_df["severity"].map(severity_order)
    alert_df = alert_df.sort_values(["severity_rank", "company_name"], ascending=[False, True])
    return alert_df.drop(columns=["severity_rank"]).reset_index(drop=True)


def generate_executive_report(risk_df: pd.DataFrame, alerts_df: pd.DataFrame, latest_month: str) -> str:
    top_company = risk_df.sort_values("risk_score", ascending=False).iloc[0]
    top_alerts = alerts_df.head(4)

    lines = [
        f"[JB Insight CRO] {latest_month} 그룹 리스크 브리프",
        "",
        "1. 종합 요약",
        f"- 이번 달 기준 최고 위험 계열사는 {top_company['company_name']}이며, 리스크 점수는 {int(top_company['risk_score'])}점, 위험 단계는 {top_company['risk_level']}입니다.",
        f"- 핵심 위험 요인은 {top_company['top_drivers_text']} 입니다.",
        f"- 전체 경보 건수는 {len(alerts_df)}건이며, 이 중 High 경보는 {len(alerts_df[alerts_df['severity'] == 'High'])}건입니다.",
        "",
        "2. 핵심 리스크 이슈",
    ]

    if len(top_alerts) == 0:
        lines.append("- 식별된 주요 경보가 없습니다.")
    else:
        for idx, (_, row) in enumerate(top_alerts.iterrows(), start=1):
            lines.append(f"- 이슈 {idx}: {row['company_name']} / {row['alert_type']} / {row['detail']}")

    lines += [
        "",
        "3. 권고 사항",
        "- 위험도 상위 계열사의 변동 지표와 로그 이슈를 우선 점검합니다.",
        "- 연체율 및 운영리스크가 동시에 상승한 포트폴리오를 집중 모니터링합니다.",
        "- 민원 및 익스포저 확대 이슈는 유형별로 세분화하여 후속 조치 체계를 정비합니다.",
    ]
    return "\n".join(lines)


def answer_question(question: str, risk_df: pd.DataFrame, alerts_df: pd.DataFrame, metrics_df: pd.DataFrame) -> str:
    top_company = risk_df.sort_values("risk_score", ascending=False).iloc[0]

    if "가장 위험한 계열사" in question:
        return (
            f"이번 달 가장 위험한 계열사는 {top_company['company_name']}입니다. "
            f"리스크 점수는 {int(top_company['risk_score'])}점이며 주요 위험 요인은 {top_company['top_drivers_text']}입니다."
        )

    if "가장 크게 악화된 지표" in question:
        metric_map = {
            "연체율": top_company["delinquency_change_pct"],
            "민원 건수": top_company["complaints_change_pct"],
            "이상 이벤트 수": top_company["abnormal_events_change_pct"],
            "부동산 익스포저": top_company["real_estate_change_pct"],
            "SME 익스포저": top_company["sme_change_pct"],
        }
        metric_name = max(metric_map, key=metric_map.get)
        return (
            f"지난달 대비 가장 크게 악화된 지표는 {top_company['company_name']}의 {metric_name}입니다. "
            f"변화율은 {metric_map[metric_name]}%입니다."
        )

    if "우선 대응" in question:
        if len(alerts_df) == 0:
            return "현재 우선 대응이 필요한 경보가 없습니다."
        top_alert = alerts_df.iloc[0]
        return (
            f"우선 대응이 필요한 리스크는 {top_alert['company_name']}의 {top_alert['alert_type']}입니다. "
            f"사유는 '{top_alert['detail']}'이며 권고 조치는 '{top_alert['recommended_action']}'입니다."
        )

    if "운영리스크" in question:
        ranked = risk_df.sort_values(["operational_score", "risk_score"], ascending=[False, False]).iloc[0]
        return (
            f"운영리스크가 가장 큰 계열사는 {ranked['company_name']}입니다. "
            f"운영리스크 점수는 {int(ranked['operational_score'])}점이며 전체 리스크 점수는 {int(ranked['risk_score'])}점입니다."
        )

    return "지원하지 않는 질문입니다."
