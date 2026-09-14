import json
import os
import time

import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials


# ============================================================
# 1. Configuration
# ============================================================

NHTSA_API_URL = (
    "https://data.transportation.gov/resource/mu99-t4jn.json"
)

GOOGLE_SHEET_ID = (
    "1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk"
)

TARGET_CAMPAIGN_PREFIX = "26T"

NHTSA_LIMIT = 5000

REQUEST_TIMEOUT = 30

MAX_RETRIES = 3


TARGET_COLUMNS = [
    "Year",
    "Report_Received_Date",
    "Manufacturer",
    "Component",
    "Campaign_Number",
    "Subject",
    "Summary",
]


# ============================================================
# 2. Google Sheets Connection
# ============================================================

def connect_google_sheet():
    """
    GitHub Secret GCP_CREDENTIALS를 이용하여
    Google Sheets에 연결한다.
    """

    credentials_json = os.environ.get("GCP_CREDENTIALS")

    if not credentials_json:
        raise RuntimeError(
            "GitHub Secret 'GCP_CREDENTIALS'를 찾을 수 없습니다."
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
            scope,
        )
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open_by_key(
        GOOGLE_SHEET_ID
    )

    return spreadsheet.sheet1


# ============================================================
# 3. NHTSA Data Request
# ============================================================

def fetch_nhtsa_data():
    """
    NHTSA API에서 최근 데이터를 가져온다.

    성공:
        list 반환

    실패:
        None 반환
    """

    params = {
        "$order": "report_received_date DESC",
        "$limit": NHTSA_LIMIT,
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(compatible; NHTSA-Recall-Dashboard/1.0)"
        ),
        "Accept": "application/json",
    }

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            print(
                f"NHTSA API 요청 중... "
                f"시도 {attempt}/{MAX_RETRIES}"
            )

            response = requests.get(
                NHTSA_API_URL,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )

            print(
                f"NHTSA HTTP 상태 코드: "
                f"{response.status_code}"
            )

            # ------------------------------------------------
            # HTTP 5xx
            # ------------------------------------------------

            if 500 <= response.status_code < 600:

                print(
                    "NHTSA 서버 오류가 발생했습니다. "
                    "잠시 후 다시 시도합니다."
                )

                if attempt < MAX_RETRIES:
                    time.sleep(3)
                    continue

                print(
                    "NHTSA API 요청이 최종적으로 실패했습니다."
                )

                return None

            # ------------------------------------------------
            # HTTP 429
            # ------------------------------------------------

            if response.status_code == 429:

                print(
                    "NHTSA API 요청 제한(429)이 발생했습니다."
                )

                if attempt < MAX_RETRIES:
                    time.sleep(5)
                    continue

                return None

            # ------------------------------------------------
            # Other HTTP Errors
            # ------------------------------------------------

            if response.status_code >= 400:

                print(
                    "NHTSA API HTTP 오류: "
                    f"{response.status_code}"
                )

                print(
                    response.text[:500]
                )

                return None

            # ------------------------------------------------
            # JSON Parsing
            # ------------------------------------------------

            try:

                data = response.json()

            except ValueError:

                print(
                    "NHTSA API 응답을 JSON으로 "
                    "변환할 수 없습니다."
                )

                print(
                    response.text[:500]
                )

                return None

            # ------------------------------------------------
            # Validate Response
            # ------------------------------------------------

            if not isinstance(data, list):

                print(
                    "NHTSA API 응답 형식이 예상과 다릅니다."
                )

                print(
                    f"응답 타입: {type(data).__name__}"
                )

                print(
                    str(data)[:500]
                )

                return None

            print(
                f"NHTSA API 데이터 수신 완료: "
                f"{len(data)}건"
            )

            return data

        except requests.exceptions.Timeout:

            print(
                "NHTSA API 요청 시간 초과가 발생했습니다."
            )

            if attempt < MAX_RETRIES:
                time.sleep(3)
                continue

            return None

        except requests.exceptions.ConnectionError:

            print(
                "NHTSA API 연결 오류가 발생했습니다."
            )

            if attempt < MAX_RETRIES:
                time.sleep(3)
                continue

            return None

        except requests.exceptions.RequestException as e:

            print(
                f"NHTSA API 요청 오류: {e}"
            )

            return None

        except Exception as e:

            print(
                f"예상하지 못한 오류가 발생했습니다: {e}"
            )

            return None

    return None


# ============================================================
# 4. Filter 2026 Tire Recalls
# ============================================================

def filter_tire_recalls(data):
    """
    NHTSA 데이터에서 26T로 시작하는
    2026년 타이어 리콜 데이터를 추출한다.
    """

    final_rows = [
        TARGET_COLUMNS
    ]

    for row in data:

        if not isinstance(row, dict):
            continue

        campaign_number = (
            str(
                row.get(
                    "nhtsa_campaign_number",
                    "",
                )
            )
            .strip()
            .upper()
        )

        # 26T = 2026년 타이어 리콜
        if not campaign_number.startswith(
            TARGET_CAMPAIGN_PREFIX
        ):
            continue

        report_received_date = (
            str(
                row.get(
                    "report_received_date",
                    "",
                )
            )
            .strip()
        )

        if report_received_date:
            report_received_date = (
                report_received_date[:10]
            )

        manufacturer = str(
            row.get(
                "manufacturer",
                row.get(
                    "mfr_name",
                    "",
                ),
            )
        ).strip()

        component = str(
            row.get(
                "component",
                "",
            )
        ).strip()

        subject = str(
            row.get(
                "subject",
                "",
            )
        ).strip()

        summary = str(
            row.get(
                "summary",
                row.get(
                    "recall_description",
                    "",
                ),
            )
        ).strip()

        final_rows.append(
            [
                "2026",
                report_received_date,
                manufacturer,
                component,
                campaign_number,
                subject,
                summary,
            ]
        )

    return final_rows


# ============================================================
# 5. Remove Duplicate Campaign Numbers
# ============================================================

def deduplicate_rows(rows):
    """
    동일한 Campaign_Number가 여러 번 존재하는 경우
    중복을 제거한다.
    """

    if len(rows) <= 1:
        return rows

    header = rows[0]

    campaign_index = (
        header.index("Campaign_Number")
    )

    unique_rows = [
        header
    ]

    seen_campaigns = set()

    for row in rows[1:]:

        campaign_number = (
            str(
                row[campaign_index]
            )
            .strip()
            .upper()
        )

        if not campaign_number:
            continue

        if campaign_number in seen_campaigns:
            continue

        seen_campaigns.add(
            campaign_number
        )

        unique_rows.append(row)

    return unique_rows


# ============================================================
# 6. Update Google Sheets
# ============================================================

def update_google_sheet(
    sheet,
    final_rows,
):
    """
    Google Sheets를 업데이트한다.

    데이터가 0건이면 기존 데이터를 삭제하지 않는다.
    """

    data_count = (
        len(final_rows) - 1
    )

    # --------------------------------------------------------
    # 안전장치
    # --------------------------------------------------------

    if data_count <= 0:

        print(
            "⚠️ 26T 리콜 데이터가 0건입니다."
        )

        print(
            "기존 Google Sheets 데이터를 "
            "삭제하지 않습니다."
        )

        return

    print(
        f"Google Sheets 업데이트 시작: "
        f"{data_count}건"
    )

    # --------------------------------------------------------
    # 기존 데이터 삭제
    # --------------------------------------------------------

    sheet.clear()

    # --------------------------------------------------------
    # 새로운 데이터 입력
    # --------------------------------------------------------

    try:

        sheet.update(
            range_name="A1",
            values=final_rows,
        )

    except TypeError:

        # gspread 버전 호환
        sheet.update(
            "A1",
            final_rows,
        )

    print(
        f"✅ Google Sheets 업데이트 완료: "
        f"{data_count}건"
    )


# ============================================================
# 7. Main
# ============================================================

def main():

    print(
        "============================================"
    )

    print(
        "NHTSA 2026 타이어 리콜 데이터 업데이트 시작"
    )

    print(
        "============================================"
    )

    # --------------------------------------------------------
    # 1. NHTSA API 데이터 가져오기
    # --------------------------------------------------------

    data = fetch_nhtsa_data()

    # --------------------------------------------------------
    # API 실패 시
    # --------------------------------------------------------

    if data is None:

        print(
            "⚠️ NHTSA API 데이터를 가져오지 못했습니다."
        )

        print(
            "기존 Google Sheets 데이터를 "
            "그대로 유지합니다."
        )

        return

    # --------------------------------------------------------
    # 2. 26T 필터링
    # --------------------------------------------------------

    final_rows = filter_tire_recalls(
        data
    )

    print(
        f"26T 타이어 리콜 필터링 결과: "
        f"{len(final_rows) - 1}건"
    )

    # --------------------------------------------------------
    # 3. 중복 제거
    # --------------------------------------------------------

    final_rows = deduplicate_rows(
        final_rows
    )

    print(
        f"중복 제거 후 데이터: "
        f"{len(final_rows) - 1}건"
    )

    # --------------------------------------------------------
    # 4. 데이터가 없는 경우
    # --------------------------------------------------------

    if len(final_rows) <= 1:

        print(
            "⚠️ 2026년 타이어 리콜 데이터가 "
            "현재 조회되지 않았습니다."
        )

        print(
            "Google Sheets 기존 데이터를 "
            "삭제하지 않습니다."
        )

        return

    # --------------------------------------------------------
    # 5. Google Sheets 연결
    # --------------------------------------------------------

    print(
        "Google Sheets 연결 중..."
    )

    sheet = connect_google_sheet()

    print(
        "Google Sheets 연결 성공"
    )

    # --------------------------------------------------------
    # 6. Google Sheets 업데이트
    # --------------------------------------------------------

    update_google_sheet(
        sheet,
        final_rows,
    )

    print(
        "============================================"
    )

    print(
        "🎉 전체 데이터 업데이트 작업 완료"
    )

    print(
        "============================================"
    )


# ============================================================
# 8. Execute
# ============================================================

if __name__ == "__main__":
    main()
