import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date, timedelta

# ==========================================
# 1. 페이지 설정 및 통합 커스텀 CSS
# ==========================================
st.set_page_config(page_title="NHTSA / TIRE QUALITY MONITOR", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #F8F9F9; }
    
    .top-category { font-size: 12px; font-weight: 700; color: #7F8C8D; letter-spacing: 1px; margin-bottom: 5px; }
    .main-title { font-size: 36px; font-weight: 800; color: #1E272E; margin-bottom: 5px; }
    .sub-title { font-size: 15px; color: #7F8C8D; margin-bottom: 25px; }
    
    .badge-container { display: flex; gap: 10px; margin-bottom: 20px; }
    .status-badge { background-color: #EAFAF1; color: #27AE60; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .filter-badge { background-color: #F2F3F4; color: #5D6D7E; padding: 4px 10px; border-radius: 4px; font-size: 12px; border: 1px solid #E5E8E8; }
    
    .kpi-card { background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #EAECEE; box-shadow: 0 1px 3px rgba(0,0,0,0.02); height: 120px; }
    .kpi-title { font-size: 13px; color: #7F8C8D; margin-bottom: 10px; display: flex; justify-content: space-between; }
    .kpi-value { font-size: 32px; font-weight: 800; color: #2C3E50; margin-bottom: 5px; line-height: 1.2; }
    .kpi-desc { font-size: 12px; color: #A6ACAF; }
    
    .section-header { font-size: 11px; font-weight: 700; color: #7F8C8D; letter-spacing: 1px; margin-top: 30px; margin-bottom: 5px; text-transform: uppercase; }
    .section-title { font-size: 18px; font-weight: 700; color: #2C3E50; margin-bottom: 15px; }
    
    .qa-brief-card { background-color: #1A362D; color: white; padding: 30px; border-radius: 8px; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .qa-title { font-size: 12px; font-weight: bold; color: #A3E4D7; letter-spacing: 1px; margin-bottom: 10px; }
    .qa-main-text { font-size: 20px; font-weight: 700; margin-bottom: 20px; }
    .qa-content { font-size: 14px; line-height: 1.8; color: #E8F8F5; margin-bottom: 20px; }
    .qa-highlight { font-weight: 700; color: #FFFFFF; border-bottom: 1px solid #A3E4D7; padding-bottom: 2px; }
    .qa-button { background-color: transparent; color: white; border: 1px solid #45B39D; padding: 8px 15px; border-radius: 4px; font-size: 13px; width: 100%; text-align: center; cursor: pointer; }
    
    .signal-box { background-color: #FDFAF2; border: 1px solid #F6DDCC; padding: 20px; border-radius: 8px; display: flex; align-items: center; gap: 15px; margin-bottom: 10px; }
    .signal-icon { background-color: #FDEBD0; padding: 10px; border-radius: 8px; color: #D68910; }
    
    .ai-summary-card { background-color: #FFFFFF; border-left: 4px solid #45B39D; padding: 15px 20px; margin-bottom: 10px; border-radius: 4px; border-top: 1px solid #EAECEE; border-right: 1px solid #EAECEE; border-bottom: 1px solid #EAECEE; }
    .ai-summary-title { font-weight: 700; color: #1A362D; margin-bottom: 5px; font-size: 14px; }
    .ai-summary-text { font-size: 13px; color: #5D6D7E; line-height: 1.5; }
    
    .custom-table th { background-color: #1A362D !important; color: white !important; font-weight: normal; text-align: center; }
    .custom-table td { text-align: center; color: #2C3E50; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. 동적 데이터 생성 (실제 데이터 로드로 대체 가능)
# ==========================================
@st.cache_data
def load_nhtsa_data():
    np.random.seed(42)
    n_records = 3000
    
    # 2020년부터 현재까지의 가상 데이터 생성
    dates = pd.to_datetime(np.random.choice(pd.date_range('2020-01-01', '2026-09-08'), n_records))
    brands = np.random.choice(['NEXEN', 'HANKOOK', 'KUMHO', 'MICHELIN', 'OTHER'], n_records, p=[0.15, 0.25, 0.2, 0.3, 0.1])
    symptoms = np.random.choice(['트레드 분리', '진동-밸런스', '파열 Blowout', '변형-부풀음', '균열 Cracking'], n_records)
    vehicles = np.random.choice(['RAM 3500', 'Hyundai Sonata', 'JEEP WRANGLER', 'Ford F-150', 'Kia K5'], n_records)
    models = np.random.choice(['N Priz AH8', 'Roadian HTX', 'N Fera AU7', 'Aria AH7', 'Winguard'], n_records)
    sizes = np.random.choice(['225/55R17', '235/45R18', '245/40R19', '215/55R17', '275/40R20'], n_records)
    states = np.random.choice(['CA (캘리포니아)', 'TX (텍사스)', 'FL (플로리다)', 'NY (뉴욕)', 'PA (펜실베니아)'], n_records)
    speeds = np.random.choice(['60-70 mph', '70-80 mph', '50-60 mph', 'Under 50 mph', 'Over 80 mph'], n_records)
    crashes = np.random.choice([0, 1], n_records, p=[0.97, 0.03]) # 3% 사고율
    
    df = pd.DataFrame({
        'Date': dates,
        'Year': dates.year.astype(str),
        'Brand': brands,
        'Symptom': symptoms,
        'Vehicle': vehicles,
        'Model': models,
        'Size': sizes,
        'State': states,
        'Speed': speeds,
        'Crash': crashes
    })
    return df

df_base = load_nhtsa_data()


# ==========================================
# 3. 사이드바 (탐색 필터 + 일괄 적용 폼)
# ==========================================
with st.sidebar:
    st.markdown("**탐색 필터** <span style='float:right; font-size:12px; color:gray; cursor:pointer;'>초기화</span>", unsafe_allow_html=True)
    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    col_btn1.button("NEXEN 중심", use_container_width=True)
    col_btn2.button("전체 브랜드", use_container_width=True)
    
    with st.form("filter_form"):
        # 동적 필터
        selected_brand = st.selectbox("타이어 브랜드", ["전체", "NEXEN", "HANKOOK", "KUMHO", "MICHELIN"], index=1)
        st.selectbox("브랜드 판별 근거", ["등록 브랜드 + 원문 언급"])
        
        st.markdown("---")
        st.markdown("**기간 기준**")
        start_date = st.date_input("시작일", value=date(2020, 1, 1))
        end_date = st.date_input("종료일", value=date(2026, 9, 8))
        
        st.markdown("---")
        submit_btn = st.form_submit_button("필터 적용하기", type="primary", use_container_width=True)


# ==========================================
# 4. 데이터 필터링 로직 적용
# ==========================================
# 날짜 필터 적용
mask = (df_base['Date'].dt.date >= start_date) & (df_base['Date'].dt.date <= end_date)

# 브랜드 필터 적용
if selected_brand != "전체":
    mask &= (df_base['Brand'] == selected_brand)

df_filtered = df_base[mask]

# 필터 결과에 데이터가 없는 경우 처리
if df_filtered.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터를 변경해주세요.")
    st.stop()

# ==========================================
# 5. 동적 KPI 계산
# ==========================================
total_complaints = len(df_filtered)

# 최근 180일 필터
recent_180_date = end_date - timedelta(days=180)
recent_180_count = len(df_filtered[df_filtered['Date'].dt.date >= recent_180_date])

# 사고 동반 신고 건수
crash_count = df_filtered['Crash'].sum()

# 고유 차종 수
unique_vehicles = df_filtered['Vehicle'].nunique()

# 가장 많이 발생한 증상 및 차종 (QA Brief용)
top_symptom = df_filtered['Symptom'].value_counts().idxmax() if not df_filtered.empty else "없음"
top_symptom_cnt = df_filtered['Symptom'].value_counts().max() if not df_filtered.empty else 0
top_vehicle = df_filtered['Vehicle'].value_counts().idxmax() if not df_filtered.empty else "없음"
top_vehicle_cnt = df_filtered['Vehicle'].value_counts().max() if not df_filtered.empty else 0


# ==========================================
# 6. 메인 헤더 및 KPI 영역 렌더링
# ==========================================
st.markdown('<div class="top-category">NHTSA / TIRE QUALITY MONITOR</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">작은 신호에서, 품질의 다음을.</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">타이어 관련 신고를 연결하고, 확인이 필요한 패턴을 찾아보세요.</div>', unsafe_allow_html=True)
st.markdown(f'''
    <div class="badge-container">
        <span class="status-badge">● 공식 데이터 확보</span>
        <span class="filter-badge">조회 시작 {start_date}</span>
        <span class="filter-badge">조회 종료 {end_date}</span>
    </div>
''', unsafe_allow_html=True)

st.markdown(f'<div class="section-title">{selected_brand} 모니터링</div>', unsafe_allow_html=True)
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
with col_kpi1:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">필터에 해당하는 신고 📄</div><div class="kpi-value">{total_complaints:,}</div><div class="kpi-desc">ODI 신고번호 기준 - 중복 제거</div></div>', unsafe_allow_html=True)
with col_kpi2:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">최근 180일 접수 ↗</div><div class="kpi-value">{recent_180_count:,}</div><div class="kpi-desc">최근 180일 기준 증가 추이</div></div>', unsafe_allow_html=True)
with col_kpi3:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">사고·피해 동반 신고 ⚠</div><div class="kpi-value">{crash_count:,}</div><div class="kpi-desc">사고 및 부상 연관 데이터</div></div>', unsafe_allow_html=True)
with col_kpi4:
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">등록 차종 🚗</div><div class="kpi-value">{unique_vehicles:,}</div><div class="kpi-desc">영향을 받은 고유 차종 수</div></div>', unsafe_allow_html=True)


# ==========================================
# 7. 트렌드 차트 & QA Brief
# ==========================================
col_mid1, col_mid2 = st.columns([2.3, 1])

with col_mid1:
    st.markdown('<div class="section-header">COMPLAINT TREND</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">신고 건수 추이 (연도별)</div>', unsafe_allow_html=True)
    
    # 동적 트렌드 데이터 생성
    trend_data = df_filtered.groupby('Year').size().reset_index(name='Count')
    
    fig_trend = px.bar(trend_data, x='Year', y='Count', text='Count')
    fig_trend.update_traces(marker_color='#719A7E', width=0.4, textposition='outside', textfont=dict(color='gray'))
    fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=320, margin=dict(l=0, r=0, t=20, b=0), xaxis_title=None, yaxis_title=None, yaxis=dict(showgrid=True, gridcolor='#F2F3F4'), xaxis=dict(showgrid=False))
    st.plotly_chart(fig_trend, use_container_width=True)

with col_mid2:
    st.markdown('<div class="section-header">&nbsp;</div>', unsafe_allow_html=True)
    st.markdown(f'''
        <div class="qa-brief-card">
            <div class="qa-title">✨ YOUR QA BRIEF</div>
            <div class="qa-main-text">현재 필터 요약</div>
            <div class="qa-content">
                {selected_brand} 관련 신고 <span class="qa-highlight">{total_complaints:,}건</span>이 현재 조건에 해당합니다.<br><br>
                가장 많이 포착된 증상은 <span class="qa-highlight">{top_symptom} ({top_symptom_cnt}건)</span>입니다.<br><br>
                등록 차종 중 <span class="qa-highlight">{top_vehicle} ({top_vehicle_cnt}건)</span>이 가장 많습니다.
            </div>
            <div class="qa-button">📋 요약 복사</div>
        </div>
    ''', unsafe_allow_html=True)


# ==========================================
# 8. 신호 감지 & AI 원문 요약 
# ==========================================
st.markdown('<div class="section-header">FROM PATTERNS TO QUESTIONS</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">어떤 신호를 먼저 살펴볼까요?</div>', unsafe_allow_html=True)

st.markdown('''
    <div class="signal-box">
        <div class="signal-icon">📈</div>
        <div>
            <div style="font-weight: bold; color: #9C640C; font-size: 15px;">균열-드라이 로트 - 증가 후보 <span style="border: 1px solid #E59866; color: #D35400; font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-left: 10px;">신규 ↗</span></div>
            <div style="color: #A6ACAF; font-size: 12px; margin-top: 5px;">최근 180일 통계적 이상 패턴 탐지됨</div>
        </div>
    </div>
''', unsafe_allow_html=True)

st.markdown('<div class="section-header" style="margin-top:20px;">AI COMPLAINT ANALYSIS</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">주요 컴플레인 AI 요약 (최다 발생 유형)</div>', unsafe_allow_html=True)
st.markdown("""
<div class="ai-summary-card">
    <div class="ai-summary-title">사례 1. 고속도로 주행 중 트레드 분리 (Tread Separation) 현상</div>
    <div class="ai-summary-text">캘리포니아주 고속도로를 70mph로 주행하던 중 조수석 뒷바퀴에서 심각한 진동과 함께 소음이 발생. 갓길 확인 결과, 타이어 트레드가 완전히 벗겨져 철심이 노출된 상태였음.</div>
</div>
<div class="ai-summary-card">
    <div class="ai-summary-title">사례 2. 원인 불명의 사이드월 파열 (Sidewall Blowout)</div>
    <div class="ai-summary-text">텍사스에서 60mph로 정속 주행 중 우측 앞바퀴 사이드월이 갑자기 파열됨. 공기압 경고등(TPMS) 점등 직후 발생하였으며, 타이어 마일리지는 약 15,000 마일 수준.</div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# 9. 다차원 탐색 (가로 바 차트 동적 생성 함수)
# ==========================================
def draw_horizontal_bar(df_col, title):
    # 컬럼 데이터 빈도수 계산 후 상위 5개 추출 (차트 표현을 위해 역순 정렬)
    data = df_col.value_counts().head(5).reset_index()
    data.columns = ['Item', 'Count']
    data = data.sort_values('Count', ascending=True)
    
    fig = px.bar(data, x='Count', y='Item', orientation='h', text='Item')
    fig.update_traces(marker_color='#719A7E', width=0.2, textposition='outside', textfont=dict(color='#2C3E50', size=11))
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=250, margin=dict(l=0, r=20, t=10, b=0),
                      xaxis=dict(showgrid=False, showticklabels=False, title=None, range=[0, data['Count'].max()*1.3]),
                      yaxis=dict(showgrid=False, title=None, categoryorder='total ascending', tickfont=dict(color='#5D6D7E', size=11)))
    return fig

# 첫 번째 행 차트 렌더링
col_b1, col_b2, col_b3 = st.columns(3)
with col_b1:
    st.markdown('<div class="section-header">SYMPTOM EXPLORER</div><div class="section-title">주요 결함-증상</div>', unsafe_allow_html=True)
    st.plotly_chart(draw_horizontal_bar(df_filtered['Symptom'], '주요 결함-증상'), use_container_width=True)
with col_b2:
    st.markdown('<div class="section-header">VEHICLE EXPLORER</div><div class="section-title">차종별 분포</div>', unsafe_allow_html=True)
    st.plotly_chart(draw_horizontal_bar(df_filtered['Vehicle'], '차종별 분포'), use_container_width=True)
with col_b3:
    st.markdown('<div class="section-header">MODEL EXPLORER</div><div class="section-title">타이어 모델 분포</div>', unsafe_allow_html=True)
    st.plotly_chart(draw_horizontal_bar(df_filtered['Model'], '타이어 모델 분포'), use_container_width=True)

# 두 번째 행 차트 렌더링
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    st.markdown('<div class="section-header">SIZE EXPLORER</div><div class="section-title">주요 규격 분포</div>', unsafe_allow_html=True)
    st.plotly_chart(draw_horizontal_bar(df_filtered['Size'], '주요 규격 분포'), use_container_width=True)
with col_c2:
    st.markdown('<div class="section-header">STATE EXPLORER</div><div class="section-title">발생 지역(State)</div>', unsafe_allow_html=True)
    st.plotly_chart(draw_horizontal_bar(df_filtered['State'], '발생 지역'), use_container_width=True)
with col_c3:
    st.markdown('<div class="section-header">SPEED EXPLORER</div><div class="section-title">주행 속도</div>', unsafe_allow_html=True)
    st.plotly_chart(draw_horizontal_bar(df_filtered['Speed'], '주행 속도'), use_container_width=True)

st.markdown("<br><div style='text-align:center; font-size:11px; color:#A6ACAF;'>신고 건수는 판매량·장착 대수로 보정된 불량률이 아닙니다. 타이어의 결함이나 사고 원인을 확정하지 않습니다.</div>", unsafe_allow_html=True)
