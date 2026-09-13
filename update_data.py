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

# 2. NHTSA 데이터 다운로드 (최신 5000건, 에러 유발 파라미터 제거)
url = "https://data.transportation.gov/resource/mu99-t4jn.csv"
params = {"$order": "report_received_date DESC", "$limit": 5000}
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

print("NHTSA 데이터 다운로드 중...")
res = requests.get(url, headers=headers, params=params)
df = pd.read_csv(io.StringIO(res.text))

# 3. 데이터 정제 및 2026년 타이어 필터링
df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
date_col = next((c for c in ['report_received_date', 'received_date', 'date'] if c in df.columns), None)

if date_col:
    df['Report_Received_Date'] = pd.to_datetime(df[date_col], errors='coerce')
    df['Year'] = df['Report_Received_Date'].dt.year
    df = df[df['Year'] == 2026]

# 타이어(Tire) 리콜 데이터만 추출
if 'record_type' in df.columns:
    df = df[df['record_type'].astype(str).str.upper() == 'T']
elif 'component' in df.columns:
    df = df[df['component'].astype(str).str.contains('TIRE', case=False, na=False)]

col_mapping = {'manufacturer': 'Manufacturer', 'component': 'Component', 'nhtsa_campaign_number': 'Campaign_Number', 'subject': 'Subject', 'summary': 'Summary'}
df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns}, inplace=True)

final_columns = [c for c in ['Year', 'Report_Received_Date', 'Manufacturer', 'Component', 'Campaign_Number', 'Subject', 'Summary'] if c in df.columns]
df = df[final_columns]

# 4. 구글 시트 업데이트
print("구글 시트에 데이터를 기록합니다...")
sheet.clear()

if not df.empty:
    set_with_dataframe(sheet, df)
    print(f"업데이트 성공! {len(df)}건의 타이어 리콜 데이터가 기록되었습니다.")
else:
    empty_df = pd.DataFrame(columns=final_columns)
    set_with_dataframe(sheet, empty_df)
    print("조건에 맞는 2026년 리콜 데이터가 없습니다. 제목 컬럼만 기록했습니다.")
