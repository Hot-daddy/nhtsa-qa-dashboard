import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="NHTSA Tire Quality Dashboard", layout="wide")

# ==========================================
# 1. 데이터 로드 및 전처리 (Mock Data Generator 포함)
# ==========================================
@st.cache_data
def load_data():
    """
    실제 사용 시 아래 코드를 주석 해제하고 Flat File을 로드하세요.
    df = pd.read_csv('NHTSA_Complaints.csv', low_memory=False)
    """
    # [즉시 실행을 위한 Mock 데이터 생성]
    np.random.seed(42)
    n_records = 1000
    dates = [datetime.today() - timedelta(days=int(x)) for x in np.random.randint(0, 365, n_records)]
    mfrs = np.random.choice(['NEXEN TIRE', 'MICHELIN', 'GOODYEAR', 'HANKOOK', 'KUMHO', 'CONTINENTAL'], n_records, p=[0.15, 0.25, 0.2, 0.1, 0.1, 0.2])
    brands = [mfr.split()[0] for mfr in mfrs]
    makes_models = np.random.choice(['HYUNDAI/SONATA', 'TOYOTA/CAMRY', 'FORD/F-150', 'HONDA/ACCORD', 'KIA/K5'], n_records)
    years = np.random.choice([2020, 2021, 2022, 2023, 2024, 2025, 2026], n_records)
    complaint_types = np.random.choice(['Tire Failure', 'Vehicle Control', 'Vibration', 'Other'], n_records)
    
    # 결함 키워드를 포함한 가상의 신고 원문 생성
    keywords_list = ['Tread separation', 'Blowout', 'Sidewall crack', 'Vibration', 'Pressure loss']
    descriptions = []
    for _ in range(n_records):
        kw = np.random.choice(keywords_list, p=[0.3, 0.25, 0.2, 0.15, 0.1])
        descriptions.append(f"While driving on the highway, experienced {kw.lower()} leading to {np.random.choice(['loss of control', 'a loud noise', 'forced pull over'])}.")

    df = pd.DataFrame({
        'DATE_A': dates,
        'MFR_NAME': mfrs,
        'BRAND': brands,
        'MAKE_MODEL': makes_models,
        'PROD_YEAR': years,
        'COMPLAINT_TYPE': complaint_types,
        'CDESCR': descriptions
    })
    
    df['DATE_A'] = pd.to_datetime(df['DATE_A'])
    df['YEAR_MONTH'] = df['DATE_A'].dt.to_period('M').astype(str)
    return df

df = load_data()

# ==========================================
# 2. 사이드바 필터 구성
# ==========================================
st.sidebar.header("🔍 데이터 필터")

# 날짜 필터
min_date = df['DATE_A'].min().date()
max_date = df['DATE_A'].max().date()
date_range = st.sidebar.date_input("신고 날짜 범위", [min_date, max_date], min_value=min_date, max_value=max_date)

# 제조사 / 브랜드 필터
mfr_list = st.sidebar.multiselect("제조사 (MFR_NAME)", options=df['MFR_NAME'].unique(), default=df['MFR_NAME'].unique())
brand_list = st.sidebar.multiselect("브랜드 (BRAND)", options=df['BRAND'].unique(), default=df['BRAND'].unique())

# 차종 및 생산연도 필터
make_model_list = st.sidebar.multiselect("차종 (MAKE/MODEL)", options=df['MAKE_MODEL'].unique(), default=df['MAKE_MODEL'].unique())
year_list = st.sidebar.slider("생산연도 (Year)", min_value=int(df['PROD_YEAR'].min()), max_value=int(df['PROD_YEAR'].max()), value=(2020, 2026))

# 키워드 및 신고 유형 필터
search_keyword = st.sidebar.text_input("결함 키워드 검색 (Tread separation, Blowout 등)", "")
complaint_type_list = st.sidebar.multiselect("신고 유형", options=df['COMPLAINT_TYPE'].unique(), default=df['COMPLAINT_TYPE'].unique())

# 필터 적용
mask = (
    (df['MFR_NAME'].isin(mfr_list)) &
    (df['BRAND'].isin(brand_list)) &
    (df['MAKE_MODEL'].isin(make_model_list)) &
    (df['PROD_YEAR'].between(year_list[0], year_list[1])) &
    (df['COMPLAINT_TYPE'].isin(complaint_type_list))
)

if len(date_range) == 2:
    mask = mask & (df['DATE_A'].dt.date >= date_range[0]) & (df['DATE_A'].dt.date <= date_range[1])

filtered_df = df[mask]

# 텍스트 키워드 필터 적용
if search_keyword:
    filtered_df = filtered_df[filtered_df['CDESCR'].str.contains(search_keyword, case=False, na=False)]

# ==========================================
# 3. 메인 화면 구성
# ==========================================
st.title("🚗 NHTSA 타이어 품질 모니터링 대시보드")
st.markdown("---")

if filtered_df.empty:
    st.warning("선택한 필터에 해당하는 데이터가 없습니다.")
    st.stop()

# --- KPI 카드 ---
col1, col2, col3 = st.columns(3)

# 1. 총 신고 건수
with col1:
    st.metric(label="총 신고 건수 (Complaints)", value=f"{len(filtered_df):,} 건")

# 2. 주요 결함 키워드 Top 3 도출
target_keywords = ['Tread separation', 'Blowout', 'Sidewall crack', 'Vibration', 'Pressure loss']
keyword_counts = {kw: filtered_df['CDESCR'].str.contains(kw, case=False, na=False).sum() for kw in target_keywords}
top_3_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:3]
top_3_str = ", ".join([f"{k} ({v})" for k, v in top_3_keywords])

with col2:
    st.metric(label="주요 결함 키워드 Top 3", value="자주 발생되는 이슈", delta=top_3_str, delta_color="off")

# 3. 넥센 vs 경쟁사 비중
nexen_count = len(filtered_df[filtered_df['MFR_NAME'].str.contains('NEXEN', case=False, na=False)])
total_count = len(filtered_df)
nexen_ratio = (nexen_count / total_count * 100) if total_count > 0 else 0

with col3:
    st.metric(label="넥센 타이어 신고 비중", value=f"{nexen_ratio:.1f}%", delta=f"경쟁사: {100-nexen_ratio:.1f}%", delta_color="inverse")

st.markdown("---")

# --- 시각화 (차트) ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("📈 월별 신고 건수 추이")
    trend_df = filtered_df.groupby('YEAR_MONTH').size().reset_index(name='Count')
    fig_trend = px.line(trend_df, x='YEAR_MONTH', y='Count', markers=True, 
                        title="Monthly Complaints Trend", labels={'YEAR_MONTH': 'Month', 'Count': 'Complaints'})
    st.plotly_chart(fig_trend, use_container_width=True)

with col_chart2:
    st.subheader("🏢 제조사별 신고 건수 비교")
    mfr_df = filtered_df['MFR_NAME'].value_counts().reset_index()
    mfr_df.columns = ['Manufacturer', 'Count']
    fig_mfr = px.pie(mfr_df, names='Manufacturer', values='Count', hole=0.4, title="Market Share of Complaints")
    st.plotly_chart(fig_mfr, use_container_width=True)

col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    st.subheader("📊 주요 결함 증상 빈도 (Bar Chart)")
    kw_df = pd.DataFrame(list(keyword_counts.items()), columns=['Keyword', 'Count']).sort_values(by='Count', ascending=True)
    fig_kw = px.bar(kw_df, x='Count', y='Keyword', orientation='h', title="Defect Keywords Frequency", color='Count', color_continuous_scale='Reds')
    st.plotly_chart(fig_kw, use_container_width=True)

with col_chart4:
    st.subheader("🚘 차종별 신고 건수 Top 5")
    model_df = filtered_df['MAKE_MODEL'].value_counts().head(5).reset_index()
    model_df.columns = ['Make/Model', 'Count']
    fig_model = px.bar(model_df, x='Make/Model', y='Count', title="Top 5 Vehicles with Complaints", text_auto=True)
    st.plotly_chart(fig_model, use_container_width=True)

# --- 원문 데이터 테이블 ---
st.markdown("---")
st.subheader("📝 원문 신고 데이터 (Consumer Complaints Text)")
display_cols = ['DATE_A', 'MFR_NAME', 'BRAND', 'MAKE_MODEL', 'PROD_YEAR', 'COMPLAINT_TYPE', 'CDESCR']
st.dataframe(filtered_df[display_cols].sort_values(by='DATE_A', ascending=False), use_container_width=True)
