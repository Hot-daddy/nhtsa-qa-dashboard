import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# 1. 시트 연결
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(os.environ.get("GCP_CREDENTIALS")), scope)
sheet = gspread.authorize(creds).open_by_key("1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk").sheet1

# 2. 데이터 다운로드 (★ 핵심: 최근 날짜순으로 5만건을 가져오도록 $order 복구 ★)
url = "https://data.transportation.gov/resource/mu99-t4jn.json"
params = {
    "$order": "report_received_date DESC", 
    "$limit": 50000
}
res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, params=params)
df = pd.DataFrame(res.json())

# 3. 2026년 타이어(26T) 리콜 정확하게 색출
if not df.empty and 'nhtsa_campaign_number' in df.columns:
    df = df[df['nhtsa_campaign_number'].astype(str).str.upper().str.startswith('26T')]

# 4. 컬럼명 매핑 및 정제
final_cols = ['Year', 'Report_Received_Date', 'Manufacturer', 'Component', 'Campaign_Number', 'Subject', 'Summary']

if not df.empty:
    df['Year'] = "2026"
    df.rename(columns={
        'report_received_date': 'Report_Received_Date',
        'manufacturer': 'Manufacturer',
        'component': 'Component',
        'nhtsa_campaign_number': 'Campaign_Number',
        'subject': 'Subject',
        'summary': 'Summary'
    }, inplace=True)
    
    for col in final_cols:
        if col not in df.columns:
            df[col] = ""
    df = df[final_cols]
else:
    df = pd.DataFrame(columns=final_cols)

df = df.fillna("").astype(str)

# 5. 구글 시트 강제 기록
sheet.clear()
data_to_write = [final_cols] + df.values.tolist()

try:
    sheet.update(data_to_write)
except Exception:
    sheet.update('A1', data_to_write)
