# JB Insight CRO Multi-Agent

JB금융그룹 Fin:AI Challenge 제출용 **기업금융 리스크 관제형 멀티에이전트 MVP**입니다.  
이 프로젝트는 JB우리캐피탈 기업금융 포트폴리오를 중심으로 **조기경보 탐지 → 포트폴리오 세부진단 → 대응 일정 정리 → 경영진 보고/Q&A**까지 한 흐름으로 연결합니다.

---

## 1. 한 줄 소개

> JB Insight CRO Multi-Agent는 JB우리캐피탈 기업금융 포트폴리오를 PF·담보·운전자금·조기경보·비교분석 관점으로 분해해, 실제 리스크관리 회의 화면처럼 보여주는 CRO 의사결정 지원 대시보드입니다.

---

## 2. 왜 멀티에이전트인가

기존 대시보드는 숫자와 차트를 보여주는 데는 강하지만, 아래 질문까지 자연스럽게 이어주지 못하는 경우가 많습니다.

- 왜 이번 달에 건전성이 악화되었는가
- 어떤 세그먼트를 가장 먼저 봐야 하는가
- PF와 기업대출, 담보·회수를 어떻게 나눠서 봐야 하는가
- 오늘/이번 주/다음 달에 무엇을 해야 하는가

이 프로젝트는 위 문제를 해결하기 위해 역할 분업형 구조를 사용합니다.

- **Orchestrator Agent**: 그룹 우선순위 통합
- **Portfolio Intake Agent**: 포트폴리오 구조, PF 비중, 담보 비중, 최대 익스포저 확인
- **Early Warning Agent**: 연체율, 민원, 이상 이벤트, 최근 로그 기반 경보 탐지
- **PF Surveillance Agent**: PF 브릿지론, 본PF 참여금융, 프로젝트금융 점검
- **Corporate Loan Agent**: 중소법인 담보대출, 운전자금, 설비금융 점검
- **Collateral & Recovery Agent**: 담보가치 재평가, 회수 우선순위, 포지셔닝 점검
- **Benchmark Agent**: 계열사 간 건전성 비교 및 우수사례 확인
- **Executive Reporting / Interactive Q&A Agent**: 경영진 보고 문안과 발표 질의응답 생성

### AI 엔진 구조
- **Orchestrator Agent** → `gpt-4o-mini`로 그룹 리스크 브리프 생성
- **PF / Collateral Agent** → 전문 관점 의견 생성
- **Q&A Agent** → 임원 질의 즉답
- **Scenario Agent** → 스트레스 결과 해석

---

## 3. 메인 시나리오

### 메인 계열사
- **JB우리캐피탈**

### 메인 포트폴리오 가정
- 부동산PF 브릿지론
- 본PF 참여금융
- 중소법인 부동산담보대출
- 상업용부동산 담보대출
- 설비금융·장비리스
- 건설협력업체 운전자금
- 매출채권 유동화 한도대출

### 메인 리스크 스토리
- PF 브릿지론 차환 부담 확대
- 건설협력업체 운전자금 차주군 질 저하
- 설비금융 담보가치 재평가 부담
- 담보대출 회수 프로세스 지연
- 매출채권 유동화 세그먼트 일부 정상화

---

## 4. 현재 화면 구성

### 4.1 상단 경영진 KPI
상단 KPI는 실제 회의자료 톤으로 재설계했습니다.

- 당월 최우선 점검 계열사
- 그룹 평균 위험도
- JB우리캐피탈 기업금융 연체율
- 당월 조기경보
- 전월 대비 연체율 변화
- 3개월 평균 대비 이탈
- 건전성 개선 우수사례
- 집중 관리 필요 계열사

### 4.2 탭 구조
현재 탭은 실무형 명칭으로 개편했습니다.

1. **경영진 요약**
2. **조기경보 · 계열 비교**
3. **포트폴리오 세부진단**
4. **대응계획 · 보고서 · Q&A**

### 4.3 포트폴리오 세부진단 화면
포트폴리오 탭에서는 아래 내용을 함께 봅니다.

- 연체율 변동 원인 요약
- 포트폴리오 구조 요약
- 세그먼트 상세 변화 테이블
- 세그먼트별 연체율 변화 차트
- 담보·회수 관점 포지셔닝 산포도
- 스트레스 시나리오 점검

### 4.4 대응 일정 및 보고서
분석 결과를 아래 단위로 구체화합니다.

- 오늘 실행할 항목
- 이번 주 실행할 항목
- 다음 달 재점검 항목
- 임원 보고서 출력
- 그룹 리스크 브리프
- 경영진 Q&A

### 4.5 배포 안정성 보강
배포 환경에서 자주 발생하는 문제를 줄이기 위해 아래를 반영했습니다.

- 필수 컬럼 검증
- 배포 상태 배너 및 헬스체크 요약
- 빈 데이터 fallback 처리
- 예외 발생 시 안전 래퍼 적용
- `.python-version = 3.11` 고정
- Streamlit Cloud 재배포 체크리스트 문서화

### 4.6 추가된 실전형 기능
- 경영진/그룹 브리프 PDF 다운로드
- 계열사별 리스크 히트맵
- 설정 파일(`config/risk_thresholds.json`) 분리
- 데이터 사전(`docs/data_dictionary.md`) 추가
- 단위 테스트 및 GitHub Actions CI 추가

---

## 5. JB우리캐피탈 기준 샘플 데이터 포인트

현재 샘플 데이터에는 아래 값이 반영되어 있습니다.

- 기준월: **2026-06**
- JB우리캐피탈 기업금융 연체율: **2.21%**
- 전월 대비 변화: **+0.47%p**
- 3개월 평균 대비: **+0.55%p**
- PF/프로젝트금융 비중: **34.5%**
- 담보 기반 익스포저 비중: **80.8%**
- 최대 익스포저 세그먼트: **부동산PF 브릿지론**
- 최대 익스포저 잔액: **418.0**
- 주요 악화 요인: **부동산PF 브릿지론 차환리스크 확대, 건설협력업체 운전자금 고위험 차주 비중 증가, 설비금융 담보가치 재평가 부담**
- 대표 High 경보: **PF 만기집중 경보**

---

## 6. 기술 스택

- **Frontend / Dashboard**: Streamlit
- **Data Processing**: Pandas
- **Visualization**: Plotly
- **Language**: Python
- **Data Source**: CSV 기반 샘플 데이터

---

## 7. 프로젝트 구조

```bash
jb_insight_cro/
├── app.py
├── risk_engine.py
├── requirements.txt
├── README.md
├── .python-version
├── constants.py
├── app_config.py
├── data_loader.py
├── healthcheck.py
├── ui_components.py
├── pdf_export.py
├── .github/
│   └── workflows/ci.yml
├── config/
│   └── risk_thresholds.json
├── docs/
│   └── data_dictionary.md
├── tests/
│   ├── test_config_and_loader.py
│   ├── test_pdf_export.py
│   └── test_risk_engine.py
├── .streamlit/
│   └── config.toml
└── data/
    ├── sample_risk_metrics.csv
    ├── sample_risk_logs.csv
    ├── sample_delinquency_drivers.csv
    └── sample_segment_metrics.csv
```

---

## 8. 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

실행 후 `http://localhost:8501`에서 대시보드를 확인할 수 있습니다.

---

## 9. 시연 추천 흐름

1. **경영진 요약**에서 당월 최우선 점검 계열사와 핵심 세그먼트 확인
2. **분석 워크플로우**와 **대응 일정 및 담당**으로 멀티에이전트 구조 설명
3. **조기경보 · 계열 비교**에서 그룹 위험도 분포와 월별 추이 확인
4. **포트폴리오 세부진단**에서 JB우리캐피탈 세그먼트 Drill-down 수행
5. **스트레스 시나리오 점검**으로 What-if 분석 시연
6. **대응계획 · 보고서 · Q&A**에서 임원 보고서와 그룹 브리프 확인

---

## 10. 샘플 데이터 스키마

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

## 11. 차별점

이 프로젝트의 핵심 차별점은 단순 시각화가 아니라, **기업금융 리스크를 역할별 Agent가 분업 처리하고 그 결과를 경영진 액션으로 연결한다는 점**입니다.

즉, 이 서비스는 다음을 동시에 보여줍니다.

- 어떤 계열사가 가장 위험한가
- 왜 위험해졌는가
- 어떤 세그먼트가 핵심인가
- 담보와 회수 정책으로 얼마나 방어 가능한가
- 오늘 무엇을 해야 하는가

### 11.1 실무 적용 프로세스
이 MVP는 단순 조회형 대시보드가 아니라, **월간 리스크 점검회의 / 조기경보 스크리닝 / 경영진 보고 초안 작성 / 스트레스 점검 보조**에 바로 연결될 수 있도록 설계했습니다.

- **1차 스크리닝**: Early Warning Agent가 경보, 로그, 이상징후를 요약
- **2차 진단**: PF / Collateral Agent가 세그먼트별 악화 요인을 해석
- **3차 종합판단**: Orchestrator Agent가 그룹 및 선택 계열사 우선순위를 정리
- **4차 보고/질의응답**: Executive Reporting / Q&A Agent가 보고 문안과 임원 질문 대응 초안을 생성

### 11.2 업무 가치 및 기대 효과
- **점검 우선순위 명확화**: 리스크관리자가 어느 계열사와 세그먼트를 먼저 봐야 하는지 빠르게 판단
- **보고 준비 시간 단축**: 숫자 해석, 브리프, Q&A 초안을 자동 생성해 보고 준비 시간을 절감
- **리스크 커뮤니케이션 표준화**: 같은 데이터를 보고도 다른 해석이 나오는 문제를 줄이고, 경영진 설명 포맷을 일관화
- **후속 조치 연결**: 분석에서 끝나지 않고 오늘/이번 주/다음 단계 액션까지 연결

### 11.3 운영 리스크 관리 및 검증 장치
이 프로젝트는 생성형 AI를 사용하지만, **정량 데이터 기반 초안 생성 + 사람 검토 + fallback + trace** 구조를 기본 원칙으로 둡니다.

- **정량 데이터 우선**: 연체율, 변화폭, 경보, 세그먼트 데이터 등 수치 기반 컨텍스트만 사용
- **Fallback 구조**: LLM 응답 실패 시 룰 기반 안전 출력으로 서비스 연속성 유지
- **Agent 실행 흔적 제공**: 입력, 핵심 판단, 출력 테이블을 남겨 설명가능성과 점검 가능성 확보
- **Human-in-the-loop**: 최종 여신정책/회수정책/경영 판단은 실무자 검토를 전제로 사용
- **운영 리스크 대응**: 개인정보, 보안, hallucination, 책임소재 이슈를 고려해 내부 검토형 보조도구로 활용

---

## 12. 향후 확장 방향

### 12.1 확장 로드맵
- **PoC**: JB우리캐피탈 기업금융 리스크 관제 보조도구로 시범 적용
- **Pilot**: 전북은행·광주은행 등 계열사 비교까지 확대해 그룹 관제 시나리오 검증
- **확산**: 사내 데이터, 사용자 권한, 감사 로그, 외부 거시 데이터와 연계해 운영형 서비스로 확장

### 12.2 데이터 확장 및 실연결 계획
- 현재 샘플 CSV는 **공개 지표 범위를 참고한 데모 데이터**이며, 발표/검증에 필요한 시계열·로그 밀도를 높이기 위해 확장했습니다.
- 실제 사내 데이터 연결 시에는 **data validation / standardization 계층**을 별도 확장해 컬럼 표준화, 결측치 처리, 타입 검증, 회사명 정규화, 이상치 점검을 추가할 예정입니다.
- `app.py` 화면 분리는 제출 이후 리팩토링 과제로 두고, 이번 단계에서는 데이터 밀도와 설명 가능성을 우선 강화했습니다.

### 12.3 공개 데이터 앵커 및 검증 계층 반영
- `data/public_anchor_metrics.csv`에 한국은행/ECOS 공개 지표를 최초 반영했습니다. 현재 포함된 앵커는 **한국은행 기준금리 2.50(2025-05-29)**, **ECOS 기준금리 2.50(20260612)**, **KORIBOR(3개월) 2.92(20260612)**, **회사채수익률(3년, AA-) 4.433(20260612)**, **가계대출연체율 0.4(202603)** 입니다. [한국은행 기준금리 추이](https://www.bok.or.kr/portal/singl/baseRate/list.do?dataSeCd=01&menuNo=200643) [ECOS KeyStatisticList](https://ecos.bok.or.kr/api/KeyStatisticList/MN16GNV2T0LWMVGWNQ9K/xml/kr/1/100)
- `scripts/build_anchor_params.py`는 공개 앵커 CSV를 `public_anchor_params.json`으로 변환해, 이후 합성 데이터 생성기나 시나리오 파라미터의 기준값으로 재사용할 수 있게 구성했습니다.
- `services/data_validation.py`를 신설해 필수 컬럼 검증, 날짜/숫자형 변환, 회사명 정규화, 중복 제거, 비율 범위 점검을 공통 계층으로 분리했습니다.
- 이 구조를 통해 데모 데이터라도 **공개 데이터 기반 앵커 → validation/service 계층 → 대시보드 적재** 흐름을 코드 수준에서 확인할 수 있습니다.

### 12.4 기능 확장 방향
- 실제 사내 데이터 연동
- 외부 경기/부동산/뉴스 데이터 결합
- LLM 기반 보고서 생성 고도화
- PDF / PPT 자동 생성
- 사용자 권한 관리 및 감사 로그
- 시나리오별 자본·건전성 영향 분석

---

## 13. Streamlit Cloud 장애 대응 가이드

### 13.1 권장 Python 버전
- 로컬/개발 기준 Python **3.11** 사용 권장
- 저장소 루트의 `.python-version` 파일에 `3.11` 고정
- Streamlit Community Cloud 앱 설정에서도 **Python 3.11 선택 권장**

### 13.2 흰 화면(White Screen) 발생 시 확인 순서
1. **Manage app → Reboot app** 실행
2. **Clear cache** 후 재실행
3. 브라우저 **강력 새로고침 / 시크릿 모드**로 재확인
4. 앱 첫 화면의 **배포 상태 / 헬스체크** 영역 확인
5. `metrics rows`, `risk rows`, `alerts rows` 값 확인
6. Streamlit Cloud 런타임 Python 버전이 3.11인지 확인

### 13.3 재배포 체크리스트
- 최신 커밋이 GitHub 원격 저장소에 push 되었는지 확인
- Streamlit Community Cloud에서 **Manual redeploy** 실행
- 필요 시 **Reboot + Clear cache** 병행
- 여전히 흰 화면이면 브라우저 개발자도구 Network 탭에서 JS/manifest 응답 상태 확인

### 13.4 현재 배포 반영 포인트
- 실무형 탭명 및 KPI 문구 반영
- JB우리캐피탈 기업금융 포트폴리오 현실화 데이터 반영
- 배포 상태 배너 및 헬스체크 유지
- 예외 발생 시 안전 모드 동작
