# JB Insight CRO Multi-Agent

JB금융그룹 Fin:AI Challenge 제출용 기업금융 특화 멀티에이전트 리스크 인텔리전스 MVP입니다.  
**JB Insight CRO Multi-Agent**는 PF, 기업대출, 담보·회수, 조기경보, 비교분석, 경영진 보고를 역할별 Agent로 분업해 **그룹 리스크 탐지 → 원인 해석 → 액션 아이템 제시 → 보고 자동화**를 하나의 흐름으로 연결합니다.

---

## 1. 한 줄 소개

> JB Insight CRO Multi-Agent는 JB금융그룹의 기업금융 포트폴리오를 PF·기업대출·담보·조기경보·비교분석 Agent로 분업 처리하는 멀티에이전트형 CRO 의사결정 지원 시스템입니다.

---

## 2. 왜 멀티에이전트인가

기존 리스크 대시보드는 숫자를 보여주는 데 강하지만, **왜 나빠졌는지**, **어디를 먼저 봐야 하는지**, **오늘 무엇을 해야 하는지**까지 연결하지 못하는 경우가 많습니다.

이 프로젝트는 이를 해결하기 위해 아래 구조를 사용합니다.

- **Orchestrator Agent**: 전체 우선순위 통합
- **Portfolio Intake Agent**: PF 비중, 담보 비중, 최대 익스포저 세그먼트 해석
- **Early Warning Agent**: 연체율·민원·이상 이벤트 기반 경보 탐지
- **PF Surveillance Agent**: PF 브릿지론 / 본PF / 프로젝트금융 악화 신호 추적
- **Corporate Loan Agent**: SME 운전자금, 담보부 시설자금, 일반 기업대출 해석
- **Collateral & Recovery Agent**: 담보 재평가, 회수정책, 방어력 점검
- **Benchmark Agent**: 계열사 간 비교, 개선/악화 벤치마크 추출
- **Executive Reporting / Interactive Q&A Agent**: 보고서·발표·질의응답 생성

---

## 3. 메인 데모 스토리

### 메인 계열사
- **JB우리캐피탈**

### 메인 시나리오
- PF 브릿지론 악화 신호 포착
- 기업 운전자금 브릿지론과 담보대출 구조 동시 점검
- 담보 재평가 및 회수 우선순위 제안
- 경영진용 브리프와 심사위원용 질의응답으로 마무리

---

## 4. 핵심 기능

### 4.1 Agent 실행 순서 패널
각 Agent별로 아래 정보를 한 줄씩 보여줍니다.
- 주요 입력
- 핵심 판단
- 출력 결과

### 4.2 실무 액션 아이템 자동화
분석 결과를 아래 단위로 구체화합니다.
- 오늘 점검할 항목
- 이번 주 실행할 항목
- 다음 달 재점검할 항목

### 4.3 심사위원 데모 모드
사이드바 버튼으로 시연 흐름을 빠르게 전개할 수 있습니다.
- Step 1. 그룹 스캔
- Step 2. PF/기업대출 분석
- Step 3. 담보/회수 우선순위
- Step 4. 경영진 보고

### 4.4 What-if 시뮬레이션
다음 스트레스 시나리오를 가정해 예상 연체율과 위험 단계를 재계산합니다.
- PF 차환 부담 증가
- 담보 회수율 저하
- SME 업황 악화

### 4.5 배포 안정성 보강
배포 환경에서 자주 발생하는 스키마 이슈를 줄이기 위해 아래를 반영했습니다.
- 필수 컬럼 검증
- Streamlit 테마 설정 파일 추가
- 세그먼트 스키마 backward compatibility 처리

---

## 5. 기술 스택

- **Frontend / Dashboard**: Streamlit
- **Data Processing**: Pandas
- **Visualization**: Plotly
- **Language**: Python
- **Data Source**: CSV 기반 샘플 데이터

---

## 6. 프로젝트 구조

```bash
jb_insight_cro/
├── app.py
├── risk_engine.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
└── data/
    ├── sample_risk_metrics.csv
    ├── sample_risk_logs.csv
    ├── sample_delinquency_drivers.csv
    └── sample_segment_metrics.csv
```

---

## 7. 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

실행 후 `http://localhost:8501`에서 대시보드를 확인할 수 있습니다.

---

## 8. 시연 추천 흐름

1. **Orchestrator Brief**에서 메인 Watchlist 확인
2. **Agent 실행 순서 패널**로 멀티에이전트 구조 설명
3. **실행 액션 아이템**으로 실무 연결성 강조
4. **PF · Corporate Loan · Collateral Agents** 탭에서 Drill-down 수행
5. **What-if 시뮬레이션**으로 의사결정 지원 성격 강조
6. **Executive Reporting & Q&A Agent**로 마무리

---

## 9. 샘플 데이터 스키마

### sample_risk_metrics.csv
```csv
date,company_name,company_type,delinquency_rate,complaints,abnormal_events,exposure_real_estate,exposure_sme
```

### sample_risk_logs.csv
```csv
date,company_name,issue_type,severity,description
```

### sample_delinquency_drivers.csv
```csv
date,company_name,driver_name,direction,contribution_bps,description
```

### sample_segment_metrics.csv
```csv
date,company_name,portfolio_group,segment_name,collateral_type,industry,balance,delinquency_rate,customer_count
```

---

## 10. 차별점

이 프로젝트의 핵심 차별점은 단순 시각화가 아니라, **기업금융 리스크를 역할별 Agent가 분업 처리하고 그 결과를 경영진 액션으로 연결한다는 점**입니다.

즉, 이 서비스는 다음을 동시에 보여줍니다.
- 어떤 계열사가 가장 위험한가
- 왜 위험해졌는가
- 어떤 세그먼트가 핵심인가
- 담보와 회수 정책으로 얼마나 방어 가능한가
- 오늘 무엇을 해야 하는가

---

## 11. 향후 확장 방향

- 실제 사내 데이터 연동
- 외부 경기/부동산/뉴스 데이터 결합
- LLM 기반 보고서 생성 고도화
- PDF / PPT 자동 생성
- 사용자 권한 관리 및 감사 로그
- 시나리오별 자본·건전성 영향 분석
