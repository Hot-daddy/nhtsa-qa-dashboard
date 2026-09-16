# NHTSA Tire Quality Dashboard

NHTSA의 2026년 타이어 리콜과 2020년 이후 타이어 소비자 불만을 정기적으로
수집해 Google Sheets에 저장하고, Streamlit에서 브랜드 및 NEXEN 패턴별로
분석하는 프로젝트입니다.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `update_data.py` | Socrata API에서 `26T` 리콜을 수집해 첫 번째 시트에 저장 |
| `update_complaints.py` | NHTSA 불만 ZIP을 수집·정규화해 `Tire_Complaints` 탭에 안전하게 교체 |
| `pattern_master.csv` | NEXEN 패턴명 및 별칭 표준화 사전 |
| `app.py` | 리콜·불만·브랜드·NEXEN 패턴 분석 Streamlit 대시보드 |
| `.github/workflows/update.yml` | 매주 금요일 미국 동부시간 정오 및 수동 실행 |
| `requirements.txt` | Python 패키지 의존성 |

## 최초 설정

1. Google 서비스 계정 이메일에 대상 Google Sheet의 편집 권한을 부여합니다.
2. GitHub 저장소의 `Settings > Secrets and variables > Actions`에서
   `GCP_CREDENTIALS`라는 Repository secret을 만들고 서비스 계정 JSON 전체를
   값으로 저장합니다.
3. Google Sheet가 Streamlit에서 CSV로 읽힐 수 있도록 보기 권한을 설정합니다.
4. GitHub Actions의 `Update NHTSA Tire Quality Data`를 수동 실행합니다.
5. 첫 번째 실행이 끝나면 첫 번째 시트에는 리콜 데이터가, `Tire_Complaints`
   탭에는 불만 데이터가 생성됩니다.

## 로컬 확인

가상환경에서 `python -m pip install -r requirements.txt`를 실행한 뒤 다음
명령을 사용할 수 있습니다.

- 실제 Google Sheets 업데이트: `python update_data.py` 및
  `python update_complaints.py`
- Sheets에 쓰지 않는 불만 데이터 검증: `python update_complaints.py --dry-run`
- Streamlit 실행: `streamlit run app.py`

Google Sheets에 쓰는 명령에는 `GCP_CREDENTIALS` 환경 변수가 필요합니다.

## 데이터 보호 원칙

- 리콜 API 실패 또는 `26T` 결과 0건이면 기존 리콜 시트를 변경하지 않습니다.
- 불만 데이터는 별도 staging 탭에 모두 기록하고 검증한 뒤 production 탭과
  교체합니다.
- 불만 데이터가 기존 대비 25% 이상 급감하면 업데이트를 중단합니다.
- Google 인증 및 권한 오류는 GitHub Actions 실패로 표시합니다.

## 해석 시 주의사항

- 불만 건수는 NHTSA `ODINO` 기준 고유 사례 수입니다.
- 하나의 사례에 여러 component 행이 있어도 한 번만 집계합니다.
- 브랜드별 건수는 판매량으로 보정되지 않아 품질률로 직접 해석할 수 없습니다.
- NEXEN 패턴 분류 결과 중 충돌·미확인 건은 대시보드에서 검토 대상으로
  표시됩니다.
