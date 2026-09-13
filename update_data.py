import pandas as pd
import requests
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# 1. 인증
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = json.loads(os.environ.get("GCP_CREDENTIALS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk").sheet1

# 2. 데이터 다운로드
url = "https://data.transportation.gov/resource/mu99-t4jn.csv"
params = {"$order": "report_received_date DESC", "$limit": 5000}
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
res = requests.get(url, headers=headers, params=params)
df = pd.read_csv(io.StringIO(res.text))

# 3. 2026년 타이어 데이터 필터링
df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
date_col = next((c for c in ['report_received_date', 'received_date', 'date'] if c in df.columns), None)

if date_col:
    df['Report_Received_Date'] = pd.to_datetime(df[date_col], errors='coerce')
    df['Year'] = df['Report_Received_Date'].dt.year
    df = df[df['Year'] == 2026]

if 'record_type' in df.columns:
    df = df[df['record_type'].astype(str).str.upper() == 'T']
elif 'component' in df.columns:
    df = df[df['component'].astype(str).str.contains('TIRE', case=False, na=False)]

col_mapping = {'manufacturer': 'Manufacturer', 'component': 'Component', 'nhtsa_campaign_number': 'Campaign_Number', 'subject': 'Subject', 'summary': 'Summary'}
df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns}, inplace=True)

final_columns = [c for c in ['Year', 'Report_Received_Date', 'Manufacturer', 'Component', 'Campaign_Number', 'Subject', 'Summary'] if c in df.columns]
df = df[final_columns]

# 날짜 데이터를 엑셀 텍스트 호환을 위해 문자열로 변환
df['Report_Received_Date'] = df['Report_Received_Date'].astype(str)

# 4. 강제 기록 (가장 확실한 방식)
sheet.clear()

# 제목(컬럼명)과 데이터를 하나의 덩어리로 결합
data_to_write = [df.columns.tolist()] + df.fillna("").values.tolist()

# 라이브러리 버전 충돌을 막기 위한 이중 안전장치
try:
    sheet.update(data_to_write)
except Exception:
    sheet.update('A1', data_to_write)
    
print("구글 시트에 강제 업데이트가 완료되었습니다!")
