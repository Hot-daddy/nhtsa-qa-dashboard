import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# 1. 시트 연결
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(os.environ.get("GCP_CREDENTIALS")), scope)
sheet = gspread.authorize(creds).open_by_key("1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk").sheet1

# 2. NHTSA 서버에 직접 '26T'(2026년 타이어) 데이터만 요청 (가장 빠르고 정확한 방식)
url = "https://data.transportation.gov/resource/mu99-t4jn.json"
params = {
    "$where": "nhtsa_campaign_number like '26T%'",
    "$limit": 1000
}
res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, params=params)
data = res.json()

# 3. 데이터 매핑 (복잡한 Pandas 인덱스 에러 원천 차단)
target_columns = ['Year', 'Report_Received_Date', 'Manufacturer', 'Component', 'Campaign_Number', 'Subject', 'Summary']
final_rows = [target_columns] # 첫 줄에 헤더(제목) 추가

# Socrata API 리스트를 하나씩 돌면서 빈칸 없이 정확하게 채워넣음
for row in data:
    campaign_num = row.get('nhtsa_campaign_number', '')
    
    # 확실하게 26T로 시작하는 데이터만 입력
    if str(campaign_num).upper().startswith('26T'):
        # 날짜가 있으면 'YYYY-MM-DD' 형태로 깔끔하게 자르기
        r_date = row.get('report_received_date', '')[:10] 
        mfg = row.get('manufacturer', row.get('mfr_name', ''))
        comp = row.get('component', '')
        subj = row.get('subject', '')
        desc = row.get('summary', row.get('recall_description', ''))
        
        final_rows.append([
            "2026",
            r_date,
            mfg,
            comp,
            campaign_num,
            subj,
            desc
        ])

# 4. 구글 시트 덮어쓰기
sheet.clear()
try:
    sheet.update(final_rows)
    print(f"업데이트 성공: 총 {len(final_rows)-1}건의 데이터가 기록되었습니다.")
except Exception:
    sheet.update('A1', final_rows)
