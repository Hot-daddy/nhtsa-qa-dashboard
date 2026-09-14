import pandas as pd
import requests
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# 1. 인증 및 연결
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = json.loads(os.environ.get("GCP_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk").sheet1

# 2. 데이터 다운로드
url = "https://data.transportation.gov/resource/mu99-t4jn.csv"
params = {"$order": "report_received_date DESC", "$limit": 5000}
headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(url, headers=headers, params=params)
df = pd.read_csv(io.StringIO(res.text))

# 3. 데이터 정제 및 필터링
df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]

# 날짜 컬럼 생성 및 2026년 필터링
date_col = next((c for c in ['report_received_date', 'received_date', 'date'] if c in df.columns), None)
if date_col:
    df['Report_Received_Date'] = pd.to_datetime(df[date_col], errors='coerce')
    df['Year'] = df['Report_Received_Date'].dt.year
    df = df[df['Year'] == 2026]
else:
    df = df.iloc[0:0] # 날짜 컬럼이 없으면 빈 데이터로 처리

# 타이어 데이터 필터링
if not df.empty:
    if 'record_type' in df.columns:
        df = df[df['record_type'].astype(str).str.upper() == 'T']
    elif 'component' in df.columns:
        df = df[df['component'].astype(str).str.contains('TIRE', case=False, na=False)]

# 4. 필수 컬럼 강제 생성 및 포맷팅 (에러 원인 해결)
col_mapping = {'manufacturer': 'Manufacturer', 'component': 'Component', 'nhtsa_campaign_number': 'Campaign_Number', 'subject': 'Subject', 'summary': 'Summary'}
df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns}, inplace=True)

target_columns = ['Year', 'Report_Received_Date', 'Manufacturer', 'Component', 'Campaign_Number', 'Subject', 'Summary']
for col in target_columns:
    if col not in df.columns:
        df[col] = "" # 컬럼이 없으면 빈 값으로 강제 생성

df = df[target_columns]

# 에러를 방지하기 위해 문자로 변환 및 빈칸(NaN) 처리
df['Report_Received_Date'] = df['Report_Received_Date'].astype(str).replace('NaT', '')
df['Year'] = df['Year'].astype(str).replace('nan', '')
df = df.fillna("")

# 5. 구글 시트 강제 기록
sheet.clear()
data_to_write = [df.columns.tolist()] + df.values.tolist()

try:
    sheet.update(data_to_write)
except Exception:
    sheet.update('A1', data_to_write)
