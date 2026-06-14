from pathlib import Path

APP_TITLE = "JB Insight CRO Multi-Agent"
APP_ICON = "🤖"
EXPECTED_PYTHON = "3.11"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
METRICS_PATH = DATA_DIR / "sample_risk_metrics.csv"
LOGS_PATH = DATA_DIR / "sample_risk_logs.csv"
DRIVERS_PATH = DATA_DIR / "sample_delinquency_drivers.csv"
SEGMENT_PATH = DATA_DIR / "sample_segment_metrics.csv"
PUBLIC_ANCHOR_PATH = DATA_DIR / "public_anchor_metrics.csv"
CONFIG_DIR = BASE_DIR / "config"
DOCS_DIR = BASE_DIR / "docs"
RISK_CONFIG_PATH = CONFIG_DIR / "risk_thresholds.json"
DATA_DICTIONARY_PATH = DOCS_DIR / "data_dictionary.md"

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
    "전체 흐름": "그룹 스캔부터 포트폴리오 진단, 대응 계획, 경영진 보고까지 전 흐름을 점검하는 기본 모드입니다.",
    "Step 1. 그룹 스캔": "그룹 기준 최고 위험 계열사, 경보 건수, 비교 랭킹을 먼저 보여주는 시작 장면입니다.",
    "Step 2-1. PF 집중 점검": "PF 포트폴리오, 브릿지론, 차환 리스크 중심으로 drill-down 하는 장면입니다.",
    "Step 2-2. 기업대출 점검": "기업대출·SME 세그먼트와 업종별 취약 차주군을 점검하는 장면입니다.",
    "Step 3. 담보·회수 우선순위": "담보 재평가와 회수정책 우선순위를 제시하는 장면입니다.",
    "Step 4. 경영진 보고": "임원 보고와 질의응답으로 마무리하는 장면입니다.",
}

FOCUS_MODE_TO_DEMO = {
    "그룹 스캔": "Step 1. 그룹 스캔",
    "PF 집중 점검": "Step 2-1. PF 집중 점검",
    "기업대출 점검": "Step 2-2. 기업대출 점검",
    "담보·회수 점검": "Step 3. 담보/회수 우선순위",
    "경영진 보고": "Step 4. 경영진 보고",
}

RISK_HEATMAP_COLUMNS = {
    "credit_score": "신용리스크",
    "complaint_score": "민원/소비자보호",
    "operational_score": "운영리스크",
    "real_estate_score": "부동산집중",
    "sme_score": "SME집중",
    "trend_pressure_score": "추세압력",
    "log_risk_score": "이벤트로그",
}
