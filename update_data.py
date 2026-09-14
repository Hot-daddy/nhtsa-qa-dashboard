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

# 2. 데이터 다운로드 (최신 10000건 넉넉하게 확보)
url = "https://data.transportation.gov/resource/mu99-t4jn.csv"
params = {"$order": "report_received_date DESC", "$limit": 10000}
headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(url, headers=headers, params=params)
df = pd.read_csv(io.StringIO(res.text))

# 3. 데이터 컬럼명 정리
df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]

col_mapping = {
    'manufacturer': 'Manufacturer', 
    'component': 'Component', 
    'nhtsa_campaign_number': 'Campaign_Number', 
    'nhtsa_id': 'Campaign_Number',
    'subject': 'Subject', 
    'summary': 'Summary',
    'recall_description': 'Summary',
    'report_received_date': 'Report_Received_Date'
}
df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns}, inplace=True)

target_columns = ['Year', 'Report_Received_Date', 'Manufacturer', 'Component', 'Campaign_Number', 'Subject', 'Summary']
for col in target_columns:
    if col not in df.columns:
        df[col] = "" 

# 4. ★ 가장 확실한 방법: 리콜 번호가 '26T' (2026년 타이어)로 시작하는 데이터만 색출! ★
df['Campaign_Number'] = df['Campaign_Number'].astype(str).str.strip().str.upper()
df = df[df['Campaign_Number'].str.startswith('26T')]

# Year 컬럼에 2026 강제 입력 및 에러 방지 빈칸 처리
df['Year'] = "2026"
df['Report_Received_Date'] = df['Report_Received_Date'].astype(str).replace('nan', '').replace('NaT', '')
df = df.fillna("")

# 5. 구글 시트 강제 기록
sheet.clear()
data_to_write = [target_columns] + df[target_columns].values.tolist()

try:
    sheet.update(data_to_write)
except Exception:
    sheet.update('A1', data_to_write)
