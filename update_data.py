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

# 2. 데이터 다운로드 (서버에서 5만 건을 통째로 쓸어옵니다)
url = "https://data.transportation.gov/resource/mu99-t4jn.json"
params = {"$limit": 50000}
headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(url, headers=headers, params=params)
df = pd.DataFrame(res.json())

# 3. 무적의 필터링 (컬럼 이름 상관없이 모든 칸을 뒤져서 '26T' 색출)
if not df.empty:
    # 엑셀의 모든 칸(Cell) 중 '26T'로 시작하는 글자가 하나라도 있는 행(Row)만 남김
    mask = df.astype(str).apply(lambda row: row.str.strip().str.upper().str.startswith('26T').any(), axis=1)
    df = df[mask].copy()

# 4. 스마트 컬럼 매핑 (이름이 어떻게 바뀌어 들어오든 자동으로 짝을 맞춤)
target_columns = ['Year', 'Report_Received_Date', 'Manufacturer', 'Component', 'Campaign_Number', 'Subject', 'Summary']

if df.empty:
    df_final = pd.DataFrame(columns=target_columns)
else:
    cols = df.columns.str.lower()
    df.columns = cols
    
    # 각 데이터의 의미를 유추하여 자동 연결
    nhtsa_col = next((c for c in cols if 'id' in c or 'campaign' in c), None)
    date_col = next((c for c in cols if 'date' in c), None)
    mfg_col = next((c for c in cols if 'mfr' in c or 'manuf' in c), None)
    comp_col = next((c for c in cols if 'comp' in c), None)
    sub_col = next((c for c in cols if 'sub' in c), None)
    sum_col = next((c for c in cols if 'sum' in c or 'desc' in c), None)
    
    df_final = pd.DataFrame()
    df_final['Year'] = ["2026"] * len(df)
    df_final['Report_Received_Date'] = df[date_col] if date_col else ""
    df_final['Manufacturer'] = df[mfg_col] if mfg_col else ""
    df_final['Component'] = df[comp_col] if comp_col else ""
    df_final['Campaign_Number'] = df[nhtsa_col] if nhtsa_col else ""
    df_final['Subject'] = df[sub_col] if sub_col else ""
    df_final['Summary'] = df[sum_col] if sum_col else ""

# 에러 방지를 위해 모두 문자로 변환
df_final = df_final.fillna("").astype(str)

# 5. 구글 시트 덮어쓰기
sheet.clear()
data_to_write = [target_columns] + df_final.values.tolist()

try:
    sheet.update(data_to_write)
    print(f"성공! {len(df_final)}건의 2026년 타이어 리콜 데이터가 입력되었습니다.")
except Exception:
    sheet.update('A1', data_to_write)
