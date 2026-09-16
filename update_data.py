import json
import os
import time

import gspread
import requests


NHTSA_API_URL = "https://data.transportation.gov/resource/6axg-epim.json"
GOOGLE_SHEET_ID = "1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk"
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


def connect_google_sheet():
    """Connect to the first worksheet using the GitHub Actions secret."""
    credentials_json = os.environ.get("GCP_CREDENTIALS")

    if not credentials_json:
        raise RuntimeError("GitHub Secret 'GCP_CREDENTIALS'를 찾을 수 없습니다.")

    try:
        credentials_dict = json.loads(credentials_json)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "GCP_CREDENTIALS가 올바른 JSON 형식이 아닙니다."
        ) from exc

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    try:
        client = gspread.service_account_from_dict(
            credentials_dict,
            scopes=scopes,
        )
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        return spreadsheet.sheet1
    except Exception as exc:
        raise RuntimeError(
            "Google Sheets 인증 또는 연결에 실패했습니다. "
            "서비스 계정에 시트 편집 권한이 있는지 확인하세요."
        ) from exc


def fetch_nhtsa_data():
    """Fetch the latest recall rows from the NHTSA Socrata dataset."""
    params = {
        "$select": (
            "report_received_date,manufacturer,component,nhtsa_id,"
            "subject,defect_summary,recall_type"
        ),
        "$order": "report_received_date DESC",
        "$limit": NHTSA_LIMIT,
    }
    headers = {
        "User-Agent": "NHTSA-Recall-Dashboard/1.0",
        "Accept": "application/json",
    }

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"NHTSA API 요청 중... 시도 {attempt}/{MAX_RETRIES}")
            response = requests.get(
                NHTSA_API_URL,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            print(f"NHTSA HTTP 상태 코드: {response.status_code}")

            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(
                    f"재시도 가능한 HTTP 오류: {response.status_code}",
                    response=response,
                )

            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                raise ValueError(
                    f"예상하지 못한 응답 형식: {type(data).__name__}"
                )

            if not data:
                raise ValueError("NHTSA API가 빈 목록을 반환했습니다.")

            print(f"NHTSA API 데이터 수신 완료: {len(data)}건")
            return data

        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            print(f"NHTSA API 요청 실패: {exc}")

            if attempt < MAX_RETRIES:
                wait_seconds = 2**attempt
                print(f"{wait_seconds}초 후 다시 시도합니다.")
                time.sleep(wait_seconds)

    raise RuntimeError(
        "NHTSA API 요청이 최종적으로 실패했습니다. "
        "Google Sheets의 기존 데이터는 변경하지 않았습니다."
    ) from last_error


def normalize_text(value):
    """Convert a nullable API value to trimmed text."""
    if value is None:
        return ""
    return str(value).strip()


def filter_tire_recalls(data):
    """Build rows for 2026 tire campaigns whose NHTSA ID starts with 26T."""
    rows_by_campaign = {}

    for row in data:
        if not isinstance(row, dict):
            continue

        campaign_number = normalize_text(row.get("nhtsa_id")).upper()

        if not campaign_number.startswith(TARGET_CAMPAIGN_PREFIX):
            continue

        report_received_date = normalize_text(
            row.get("report_received_date")
        )[:10]

        rows_by_campaign[campaign_number] = [
            "2026",
            report_received_date,
            normalize_text(row.get("manufacturer")),
            normalize_text(row.get("component")),
            campaign_number,
            normalize_text(row.get("subject")),
            normalize_text(row.get("defect_summary")),
        ]

    rows = list(rows_by_campaign.values())
    rows.sort(key=lambda row: (row[1], row[4]), reverse=True)
    return [TARGET_COLUMNS, *rows]


def validate_rows(rows):
    """Stop before touching Google Sheets when collected data is suspicious."""
    if not rows or rows[0] != TARGET_COLUMNS:
        raise RuntimeError("출력 데이터의 헤더 구조가 올바르지 않습니다.")

    data_rows = rows[1:]

    if not data_rows:
        raise RuntimeError(
            "26T 리콜 데이터가 0건입니다. "
            "Google Sheets의 기존 데이터는 변경하지 않았습니다."
        )

    for row_number, row in enumerate(data_rows, start=2):
        if len(row) != len(TARGET_COLUMNS):
            raise RuntimeError(f"{row_number}행의 컬럼 수가 올바르지 않습니다.")

        campaign_number = row[4]
        if not campaign_number.startswith(TARGET_CAMPAIGN_PREFIX):
            raise RuntimeError(
                f"{row_number}행에 잘못된 Campaign Number가 있습니다: "
                f"{campaign_number}"
            )


def update_google_sheet(sheet, rows):
    """Write new data first, then remove only obsolete trailing rows."""
    old_row_count = len(sheet.get_all_values())
    new_row_count = len(rows)
    data_count = new_row_count - 1

    print(f"Google Sheets 업데이트 시작: {data_count}건")

    # Write first. If this request fails, the sheet was not cleared beforehand.
    sheet.update(
        values=rows,
        range_name=f"A1:G{new_row_count}",
        value_input_option="RAW",
    )

    # Remove obsolete trailing rows only after a successful write.
    if old_row_count > new_row_count:
        sheet.batch_clear([f"A{new_row_count + 1}:G{old_row_count}"])

    print(f"Google Sheets 업데이트 완료: {data_count}건")


def main():
    print("=" * 60)
    print("NHTSA 2026 타이어 리콜 데이터 업데이트 시작")
    print("=" * 60)

    data = fetch_nhtsa_data()
    rows = filter_tire_recalls(data)
    validate_rows(rows)

    print(f"26T 타이어 리콜 최종 결과: {len(rows) - 1}건")
    print("Google Sheets 연결 중...")

    sheet = connect_google_sheet()
    print("Google Sheets 연결 성공")

    update_google_sheet(sheet, rows)

    print("=" * 60)
    print("전체 데이터 업데이트 작업 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
