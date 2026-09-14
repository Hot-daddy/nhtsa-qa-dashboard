```python
import json
import logging
import os
import time

import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials


# ============================================================
# Configuration
# ============================================================

NHTSA_API_URL = (
    "https://data.transportation.gov/resource/mu99-t4jn.json"
)

GOOGLE_SHEET_ID = (
    "1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk"
)

TARGET_CAMPAIGN_PREFIX = "26T"

# NHTSA에서 최신 데이터 최대 5,000건
NHTSA_LIMIT = 5000

# HTTP 요청 timeout
REQUEST_TIMEOUT = 30

# 최대 재시도 횟수
MAX_RETRIES = 3


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# Google Sheets
# ============================================================

def connect_google_sheet():
    """
    GitHub Actions Secret의 GCP_CREDENTIALS를 사용하여
    Google Sheet에 연결한다.
    """

    credentials_json = os.environ.get("GCP_CREDENTIALS")

    if not credentials_json:
        raise RuntimeError(
            "GCP_CREDENTIALS GitHub Secret이 설정되어 있지 않습니다."
        )

    try:
        credentials_dict = json.loads(credentials_json)

    except json.JSONDecodeError as e:
        raise RuntimeError(
            "GCP_CREDENTIALS가 올바른 JSON 형식이 아닙니다."
        ) from e

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = (
        ServiceAccountCredentials
        .from_json_keyfile_dict(
            credentials_dict,
            scope
        )
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(
        GOOGLE_SHEET_ID
    )

    return spreadsheet.sheet1


# ============================================================
# NHTSA API
# ============================================================

def fetch_nhtsa_data():
    """
    NHTSA Socrata API에서 최신 5,000건을 가져온다.

    성공:
        list 반환

    실패:
        None 반환

    중요:
        API 실패 시 []를 반환하지 않는다.
        []와 API 실패를 구분하기 위해 None을 사용한다.
    """

    params = {
        "$order": "report_received_date DESC",
        "$limit": NHTSA_LIMIT,
    }

    headers = {
        "Accept": "application/json",
        "User-Agent": (
            "NHTSA-Tire-Recall-GitHubAction/1.0"
        ),
    }

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            logger.info(
                "NHTSA API 요청 "
                "(attempt %d/%d)",
                attempt,
                MAX_RETRIES
            )

            response = requests.get(
                NHTSA_API_URL,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )

            logger.info(
                "NHTSA HTTP Status: %s",
                response.status_code
            )

            # ------------------------------------------------
            # HTTP Error
            # ------------------------------------------------

            if response.status_code >= 400:

                logger.error(
                    "NHTSA API 오류: HTTP %s",
                    response.status_code
                )

                try:

                    error_data = response.json()

                    logger.error(
                        "NHTSA 오류 응답: %s",
                        error_data
                    )

                except ValueError:

                    logger.error(
                        "NHTSA 오류 응답 원문: %s",
                        response.text[:1000]
                    )

                # 5xx는 서버 일시 장애일 가능성이 있으므로 retry
                if response.status_code >= 500:

                    if attempt < MAX_RETRIES:

                        wait_seconds = 2 ** attempt

                        logger.warning(
                            "%d초 후 재시도합니다.",
                            wait_seconds
                        )

                        time.sleep(wait_seconds)

                        continue

                # 400 계열은 요청 자체의 문제일 가능성이 높으므로
                # 더 이상 retry하지 않는다.
                return None

            # ------------------------------------------------
            # JSON Parsing
            # ------------------------------------------------

            try:

                data = response.json()

            except ValueError:

                logger.error(
                    "NHTSA 응답이 올바른 JSON이 아닙니다."
                )

                logger.error(
                    "응답 내용: %s",
                    response.text[:1000]
                )

                return None

            # ------------------------------------------------
            # JSON Structure Validation
            # ------------------------------------------------

            if not isinstance(data, list):

                logger.error(
                    "예상하지 못한 NHTSA 응답 타입: %s",
                    type(data).__name__
                )

                logger.error(
                    "응답 내용: %s",
                    str(data)[:1000]
                )

                return None

            logger.info(
                "NHTSA 데이터 수신 성공: %d건",
                len(data)
            )

            return data

        # ----------------------------------------------------
        # Timeout
        # ----------------------------------------------------

        except requests.exceptions.Timeout:

            logger.error(
                "NHTSA API 요청 Timeout"
            )

            if attempt < MAX_RETRIES:

                wait_seconds = 2 ** attempt

                logger.warning(
                    "%d초 후 재시도합니다.",
                    wait_seconds
                )

                time.sleep(wait_seconds)

                continue

            return None

        # ----------------------------------------------------
        # Connection Error
        # ----------------------------------------------------

        except requests.exceptions.ConnectionError as e:

            logger.error(
                "NHTSA 연결 오류: %s",
                e
            )

            if attempt < MAX_RETRIES:

                wait_seconds = 2 ** attempt

                time.sleep(wait_seconds)

                continue

            return None

        # ----------------------------------------------------
        # Other Requests Error
        # ----------------------------------------------------

        except requests.exceptions.RequestException as e:

            logger.error(
                "NHTSA Requests 오류: %s",
                e
            )

            return None

        # ----------------------------------------------------
        # Unexpected Error
        # ----------------------------------------------------

        except Exception as e:

            logger.exception(
                "NHTSA 처리 중 예상하지 못한 오류: %s",
                e
            )

            return None

    return None


# ============================================================
# Filter 26T Tire Recalls
# ============================================================

def filter_tire_recalls(data):
    """
    NHTSA Campaign Number가 26T로 시작하는
    리콜만 추출한다.

    Google Sheet에서 사용할 컬럼명을
    여기서 명확하게 정의한다.
    """

    target_columns = [
        "Year",
        "Report_Received_Date",
        "Manufacturer",
        "Component",
        "Campaign_Number",
        "Subject",
        "Summary",
    ]

    final_rows = [target_columns]

    for row in data:

        # 예상치 못한 JSON 구조 방어
        if not isinstance(row, dict):
            continue

        # NHTSA Campaign Number
        campaign_number = str(
            row.get(
                "nhtsa_campaign_number",
                ""
            )
        ).strip().upper()

        # 26T = 2026 Tire Recall
        if not campaign_number.startswith(
            TARGET_CAMPAIGN_PREFIX
        ):
            continue

        # Report Date
        report_date = str(
            row.get(
                "report_received_date",
                ""
            )
        )[:10]

        # Manufacturer
        manufacturer = str(
            row.get(
                "manufacturer",
                row.get(
                    "mfr_name",
                    ""
                )
            )
        ).strip()

        # Component
        component = str(
            row.get(
                "component",
                ""
            )
        ).strip()

        # Subject
        subject = str(
            row.get(
                "subject",
                ""
            )
        ).strip()

        # Summary
        summary = str(
            row.get(
                "summary",
                row.get(
                    "recall_description",
                    ""
                )
            )
        ).strip()

        final_rows.append([
            "2026",
            report_date,
            manufacturer,
            component,
            campaign_number,
            subject,
            summary,
        ])

    return final_rows


# ============================================================
# Deduplicate
# ============================================================

def deduplicate_rows(rows):
    """
    Campaign_Number 기준으로 중복 제거.
    """

    if len(rows) <= 1:
        return rows

    header = rows[0]
    data_rows = rows[1:]

    campaign_index = header.index(
        "Campaign_Number"
    )

    seen = set()
    unique_rows = []

    for row in data_rows:

        campaign_number = str(
            row[campaign_index]
        ).strip().upper()

        if not campaign_number:
            continue

        if campaign_number in seen:
            continue

        seen.add(campaign_number)

        unique_rows.append(row)

    return [
        header,
        *unique_rows
    ]


# ============================================================
# Google Sheet Update
# ============================================================

def update_google_sheet(
    sheet,
    rows
):
    """
    정상적인 데이터가 확보된 경우에만 Google Sheet를 갱신한다.
    """

    record_count = len(rows) - 1

    # --------------------------------------------------------
    # 안전장치
    # --------------------------------------------------------

    if record_count <= 0:

        logger.warning(
            "26T 리콜 데이터가 0건입니다."
        )

        logger.warning(
            "기존 Google Sheet 데이터는 삭제하지 않습니다."
        )

        return False

    logger.info(
        "Google Sheet 업데이트: %d건",
        record_count
    )

    # --------------------------------------------------------
    # 기존 데이터 삭제
    # --------------------------------------------------------

    sheet.clear()

    # --------------------------------------------------------
    # 새 데이터 기록
    # --------------------------------------------------------

    try:

        # gspread v6+
        sheet.update(
            range_name="A1",
            values=rows,
            value_input_option="RAW"
        )

    except TypeError:

        # 구버전 gspread
        sheet.update(
            "A1",
            rows
        )

    logger.info(
        "Google Sheet 업데이트 완료: %d건",
        record_count
    )

    return True


# ============================================================
# Main
# ============================================================

def main():

    logger.info("=" * 60)
    logger.info(
        "NHTSA 2026 Tire Recall Pipeline 시작"
    )
    logger.info("=" * 60)

    # --------------------------------------------------------
    # 1. NHTSA 데이터 다운로드
    # --------------------------------------------------------

    data = fetch_nhtsa_data()

    # API 자체가 실패한 경우
    if data is None:

        logger.error(
            "NHTSA API 데이터를 가져오지 못했습니다."
        )

        logger.error(
            "Google Sheet는 변경하지 않습니다."
        )

        # 중요:
        # GitHub Actions에서 exit code 1을 발생시키지 않는다.
        return

    # --------------------------------------------------------
    # 2. Python에서 26T 필터
    # --------------------------------------------------------

    rows = filter_tire_recalls(data)

    logger.info(
        "26T 필터링 결과: %d건",
        len(rows) - 1
    )

    # --------------------------------------------------------
    # 3. 중복 제거
    # --------------------------------------------------------

    rows = deduplicate_rows(rows)

    logger.info(
        "중복 제거 후 최종 데이터: %d건",
        len(rows) - 1
    )

    # --------------------------------------------------------
    # 4. 데이터가 없으면 Sheet 보호
    # --------------------------------------------------------

    if len(rows) <= 1:

        logger.warning(
            "업데이트할 26T 데이터가 없습니다."
        )

        logger.warning(
            "기존 Google Sheet를 유지합니다."
        )

        return

    # --------------------------------------------------------
    # 5. Google Sheet 연결
    # --------------------------------------------------------

    try:

        sheet = connect_google_sheet()

    except Exception as e:

        logger.exception(
            "Google Sheet 연결 실패: %s",
            e
        )

        # Google Sheet 인증 실패는 실제 작업 실패이므로
        # GitHub Actions에서 실패로 표시한다.
        raise

    # --------------------------------------------------------
    # 6. Google Sheet 업데이트
    # --------------------------------------------------------

    update_google_sheet(
        sheet,
        rows
    )

    logger.info("=" * 60)
    logger.info(
        "NHTSA Pipeline 정상 완료"
    )
    logger.info(
        "최종 26T 리콜: %d건",
        len(rows) - 1
    )
    logger.info("=" * 60)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    main()
```

---

# 2. 최종 `app.py`

현재 `app.py`의 기본 방향은 좋습니다. 다만 저는 다음을 추가하겠습니다.

* Google Sheet가 비어 있거나 잘못된 형식이면 안전하게 처리
* 필수 컬럼 검증
* 날짜 정렬
* CSV 데이터에서 공백 제거
* 대시보드에 마지막 날짜 표시
* 제조사 수 계산
* 테이블에는 기존 컬럼 그대로 사용

그리고 **Google Sheet의 컬럼명은 `update_data.py`와 완전히 동일하게 유지**합니다.

```python
import streamlit as st
import pandas as pd


# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="2026 NHTSA 타이어 리콜 대시보드",
    page_icon="🚗",
    layout="wide",
)


# ============================================================
# Configuration
# ============================================================

GOOGLE_SHEET_ID = (
    "1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk"
)

GOOGLE_SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{GOOGLE_SHEET_ID}/export?format=csv"
)

EXPECTED_COLUMNS = [
    "Year",
    "Report_Received_Date",
    "Manufacturer",
    "Component",
    "Campaign_Number",
    "Subject",
    "Summary",
]


# ============================================================
# Google Sheets Data Loader
# ============================================================

@st.cache_data(ttl=3600)
def load_real_nhtsa_recalls():
    """
    Google Sheet를 CSV로 읽어온다.

    캐시:
        1시간

    반환:
        pandas DataFrame
    """

    try:

        df = pd.read_csv(
            GOOGLE_SHEET_CSV_URL
        )

        # ----------------------------------------------------
        # 빈 데이터
        # ----------------------------------------------------

        if df.empty:
            return pd.DataFrame()

        # ----------------------------------------------------
        # Column 이름 정리
        # ---------------------------
```
