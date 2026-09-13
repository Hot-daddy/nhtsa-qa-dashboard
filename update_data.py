import pandas as pd
import requests
import io
import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# 1. 구글 시트 인증 및 연결
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = json.loads(os.environ.get("GCP_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk").sheet1

# 2. NHTSA 데이터 다운로드 (최신 5000건)
url = "https://data.transportation.gov/resource/mu99-t4jn.csv"
params = {"$order": "report_received_date DESC", "$limit": 5000, "recall_type": "TIRE"}
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

print("NHTSA 데이터 다운로드 중...")
res = requests.get(url, headers=headers, params=params)

# === [진단용 출력] 어떤 데이터가 오는지 확인 ===
print("응답 상태 코드:", res.status_code)
print("응답 데이터 미리보기(최대 500자):\n", res.text[:500])

df = pd.read_csv(io.StringIO(res.text))
print("다운로드된 컬럼:", df.columns.tolist())
print("원본 첫 3줄 데이터:\n", df.head(3))

# 3. 데이터 정제 및 2026년 필터링
df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
date_col = next((c for c in ['report_received_date', 'received_date', 'date'] if c in df.columns), None)

if date_col:
    df['Report_Received_Date'] = pd.to_datetime(df[date_col], errors='coerce')
    df['Year'] = df['Report_Received_Date'].dt.year
    df = df[df['Year'] == 2026] # 2026년 데이터만 추출

print(f"2026년 필터링 후 남은 데이터 개수: {len(df)}개")

col_mapping = {'manufacturer': 'Manufacturer', 'component': 'Component', 'nhtsa_campaign_number': 'Campaign_Number', 'subject': 'Subject', 'summary': 'Summary'}
df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns}, inplace=True)

# 필수 컬럼만 유지
final_columns = [c for c in ['Year', 'Report_Received_Date', 'Manufacturer', 'Component', 'Campaign_Number', 'Subject', 'Summary'] if c in df.columns]
df = df[final_columns]

# 4. 구글 시트 업데이트 (기존 내용 지우고 덮어쓰기)
print("구글 시트에 데이터를 기록합니다...")
sheet.clear()

if not df.empty:
    set_with_dataframe(sheet, df)
    print("업데이트가 성공적으로 완료되었습니다!")
else:
    # 데이터가 0건이라도 제목(헤더)은 시트에 남겨둠
    empty_df = pd.DataFrame(columns=final_columns)
    set_with_dataframe(sheet, empty_df)
    print("2026년 리콜 데이터가 아직 없습니다. 빈 컬럼(제목)만 기록했습니다.")
