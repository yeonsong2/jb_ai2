# JB Insight CRO 데이터 사전

## 1. sample_risk_metrics.csv
| 컬럼 | 의미 | 예시 |
|---|---|---|
| date | 기준 월 | 2026-06-01 |
| company_name | 계열사명 | JB우리캐피탈 |
| company_type | 회사 유형 | Capital |
| delinquency_rate | 전사 연체율(%) | 2.21 |
| complaints | 월간 민원 건수 | 133 |
| abnormal_events | 이상 이벤트 건수 | 11 |
| exposure_real_estate | 부동산 관련 익스포저 지수 | 47 |
| exposure_sme | SME 익스포저 지수 | 31 |

## 2. sample_risk_logs.csv
| 컬럼 | 의미 |
|---|---|
| date | 이벤트 발생일 |
| company_name | 계열사명 |
| issue_type | 경보 유형 |
| severity | 중요도(High/Medium/Low) |
| description | 경보 설명 |

## 3. sample_delinquency_drivers.csv
| 컬럼 | 의미 |
|---|---|
| date | 기준 월 |
| company_name | 계열사명 |
| driver_name | 연체율 변화 원인명 |
| direction | positive / negative |
| contribution_bps | 연체율 기여도(bp) |
| description | 상세 설명 |

## 4. sample_segment_metrics.csv
| 컬럼 | 의미 |
|---|---|
| date | 기준 월 |
| company_name | 계열사명 |
| portfolio_group | 포트폴리오군 |
| segment_name | 세부 세그먼트 |
| collateral_type | 담보 유형 |
| industry | 차주 업종 |
| balance | 세그먼트 잔액 |
| delinquency_rate | 세그먼트 연체율(%) |
| customer_count | 차주 수 |

## 5. 설정 파일
- `config/risk_thresholds.json`
  - severity_weights: 경보 중요도 가중치
  - type_weights: 회사 유형별 가중치
  - risk_level_thresholds: High / Medium 분류 기준
  - ui_defaults: 기본 회사/기본 필터 값
