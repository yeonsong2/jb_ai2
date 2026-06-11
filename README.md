# JB Insight CRO

JB금융그룹 Fin:AI Challenge 제출용 MVP 프로젝트입니다.  
**JB Insight CRO**는 JB금융그룹 계열사별 리스크 데이터를 통합 분석하여, **조기경보**, **그룹 기준 우선순위화**, **경영진용 리스크 브리프 자동 생성**을 지원하는 AI 기반 의사결정 보조 서비스입니다.

---

## 1. 프로젝트 개요

금융그룹 환경에서는 계열사별로 관리되는 리스크 지표, 보고 형식, 운영 방식이 상이하여 그룹 차원의 리스크를 일관되게 파악하고 신속하게 대응하기 어렵습니다.  
JB Insight CRO는 이러한 문제를 해결하기 위해 다음 기능을 제공합니다.

- 계열사별 리스크 데이터 통합
- 이상 징후 조기 탐지
- 그룹 관점 리스크 우선순위 정렬
- 경영진용 그룹 리스크 브리프 자동 생성
- 간단한 질의응답 기반 리스크 인사이트 제공

본 프로젝트는 해커톤 제출용 **MVP(최소기능제품)** 으로, 실제 금융사 시스템 연동 대신 샘플 데이터를 기반으로 동작합니다.

---

## 2. 핵심 기능

### 2.1 계열사 리스크 통합 대시보드
- 계열사별 리스크 지표를 한 화면에서 확인
- 그룹 기준 최고 위험 계열사, 전체 경보 건수, 평균 리스크 점수 제공
- 월별 지표 추이 시각화

### 2.2 조기경보(Early Warning)
다음과 같은 주요 이상 징후를 자동 탐지합니다.
- 연체율 급증
- 민원 증가
- 이상 이벤트 증가
- 부동산 익스포저 확대
- SME 익스포저 확대
- 로그 기반 운영 이슈 반영

### 2.3 리스크 점수 산정 및 우선순위화
리스크 점수는 다음 요소를 종합 반영합니다.
- 신용리스크
- 민원/소비자보호 리스크
- 운영리스크
- 부동산 집중 리스크
- SME 집중 리스크
- 로그 이벤트 심각도
- 계열사 유형별 가중치

### 2.4 경영진 보고서 자동 생성
버튼 한 번으로 다음 항목이 포함된 브리프를 생성합니다.
- 종합 요약
- 최고 위험 계열사
- 핵심 리스크 이슈
- 권고 사항

### 2.5 AI Q&A
다음과 같은 질문에 대해 즉시 응답합니다.
- 이번 달 가장 위험한 계열사는?
- 지난달 대비 가장 크게 악화된 지표는?
- 우선 대응이 필요한 리스크는?
- 운영리스크가 가장 큰 계열사는?

---

## 3. 기술 스택

- **Frontend / Dashboard**: Streamlit
- **Data Processing**: Pandas
- **Visualization**: Plotly
- **Language**: Python
- **Data Source**: CSV 기반 샘플 데이터

---

## 4. 프로젝트 구조

```bash
jb_insight_cro/
├── app.py
├── risk_engine.py
├── requirements.txt
├── README.md
└── data/
    ├── sample_risk_metrics.csv
    └── sample_risk_logs.csv
```

### 파일 설명
- `app.py` : Streamlit 대시보드 메인 앱
- `risk_engine.py` : 리스크 점수 계산, 경보 탐지, 보고서 생성, Q&A 로직
- `requirements.txt` : 실행에 필요한 Python 패키지 목록
- `data/sample_risk_metrics.csv` : 월별 계열사 리스크 지표 샘플 데이터
- `data/sample_risk_logs.csv` : 최근 리스크 이벤트 로그 샘플 데이터

---

## 5. 실행 방법

### 5.1 가상환경 생성
```bash
python -m venv .venv
```

### 5.2 가상환경 활성화
#### macOS / Linux
```bash
source .venv/bin/activate
```

#### Windows PowerShell
```bash
.venv\Scripts\Activate.ps1
```

### 5.3 패키지 설치
```bash
pip install -r requirements.txt
```

### 5.4 앱 실행
```bash
streamlit run app.py
```

실행 후 브라우저에서 기본 주소(`http://localhost:8501`)로 접속하면 대시보드를 확인할 수 있습니다.

---

## 6. 샘플 데이터 스키마

### 6.1 sample_risk_metrics.csv
```csv
date,company_name,company_type,delinquency_rate,complaints,abnormal_events,exposure_real_estate,exposure_sme
```

#### 컬럼 설명
- `date`: 기준 일자
- `company_name`: 계열사명
- `company_type`: 계열사 유형
- `delinquency_rate`: 연체율
- `complaints`: 민원 건수
- `abnormal_events`: 이상 이벤트 수
- `exposure_real_estate`: 부동산 익스포저
- `exposure_sme`: 중소기업 익스포저

### 6.2 sample_risk_logs.csv
```csv
date,company_name,issue_type,severity,description
```

#### 컬럼 설명
- `date`: 이슈 발생 일자
- `company_name`: 계열사명
- `issue_type`: 이슈 유형
- `severity`: 심각도(High / Medium / Low)
- `description`: 상세 설명

---

## 7. 시연 포인트

발표 또는 시연 시 아래 순서로 확인하면 서비스 흐름을 효과적으로 보여줄 수 있습니다.

1. 메인 대시보드에서 그룹 기준 최고 위험 계열사 확인
2. 계열사별 리스크 랭킹 및 주요 위험 요인 확인
3. 조기경보 카드에서 High / Medium 경보 확인
4. 경영진 보고서 자동 생성 버튼 실행
5. AI Q&A를 통해 핵심 질문에 대한 답변 확인

---

## 8. 기대 효과

- 계열사별 리스크 데이터의 통합 가시성 확보
- 조기경보 기반 선제 대응 지원
- 경영진 보고서 작성 효율 향상
- 그룹 차원의 리스크 우선순위 판단 지원
- 반복 업무 자동화를 통한 실무 효율성 개선

---

## 9. MVP 한계 및 향후 확장 방향

### 현재 MVP 범위
- 샘플 데이터 기반 동작
- 룰 기반 및 가중치 기반 리스크 점수 산정
- 발표용/데모용 구조 중심 구현

### 향후 확장 방향
- 실제 계열사 데이터 연동
- 실시간 데이터 파이프라인 구축
- 외부 경제지표 및 뉴스 연계
- PDF 보고서 자동 내보내기
- 사용자 권한 및 감사 로그 기능 추가
- 리스크 설명 가능성 및 의사결정 지원 기능 고도화

---

## 10. 해커톤 제출 관점의 차별점

JB Insight CRO는 단순 시각화 대시보드가 아니라, **그룹 관점의 리스크 탐지 → 우선순위화 → 보고 자동화**를 하나의 흐름으로 연결한 MVP입니다.  
이를 통해 JB금융그룹의 계열사 시너지 관점에서, 리스크 관리 업무를 보다 빠르고 일관되게 수행할 수 있는 가능성을 제시합니다.

---

## 11. 서비스 한 줄 소개

**JB Insight CRO는 JB금융그룹 계열사 리스크 데이터를 통합 분석하여, 조기경보와 경영진 보고 자동화를 지원하는 AI 기반 리스크 인텔리전스 MVP입니다.**
