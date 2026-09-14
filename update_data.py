import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# 1. 인증 및 구글 시트 연결
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(os.environ.get("GCP_CREDENTIALS")), scope)
sheet = gspread.authorize(creds).open_by_key("1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk").sheet1

# 2. 데이터 다운로드 (서버 에러 방지를 위해 조건 없이 최신 5000건 가져오기)
url = "https://data.transportation.gov/resource/mu99-t4jn.json"
params = {"$order": "report_received_date DESC", "$limit": 5000}
res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, params=params)

try:
    data = res.json()
except Exception:
    data = []

# 3. 데이터 필터링 (파이썬 내부에서 안전하게 추출)
target_columns = ['Year', 'Report_Received_Date', 'Manufacturer', 'Component', 'Campaign_Number', 'Subject', 'Summary']
final_rows = [target_columns] # 첫 줄은 제목

# 서버 응답이 정상적인 리스트 형태일 때만 실행 (에러 튕김 방지)
if isinstance(data, list):
    for row in data:
        camp_num = str(row.get('nhtsa_campaign_number', '')).strip().upper()
        
        # 캠페인 넘버가 26T(2026년 타이어)로 시작하는 데이터만 색출
        if camp_num.startswith('26T'):
            r_date = str(row.get('report_received_date', ''))[:10]
            mfg = str(row.get('manufacturer', row.get('mfr_name', '')))
            comp = str(row.get('component', ''))
            subj = str(row.get('subject', ''))
            desc = str(row.get('summary', row.get('recall_description', '')))
            
            final_rows.append(["2026", r_date, mfg, comp, camp_num, subj, desc])

# 4. 구글 시트 기록 (gspread 버전별 호환성 처리)
sheet.clear()
try:
    # 최신 gspread v6+ 방식
    sheet.update(range_name='A1', values=final_rows)
except TypeError:
    # 구버전 gspread 방식
    sheet.update('A1', final_rows)

print(f"업데이트 완료: {len(final_rows)-1}건의 데이터 기록 성공")
