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
    .main-title { font-size: 34px; font-weight: 800; color: #1E272E; margin-bottom: 5px; }
    .sub-title { font-size: 14px; color: #7F8C8D; margin-bottom: 20px; }
    .badge-container { display: flex; gap: 8px; margin-bottom: 15px; }
    .status-badge { background-color: #EAFAF1; color: #27AE60; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .filter-badge { background-color: #F2F3F4; color: #5D6D7E; padding: 4px 10px; border-radius: 4px; font-size: 12px; border: 1px solid #E5E8E8; }
    .kpi-card { background-color: white; padding: 18px; border-radius: 8px; border: 1px solid #EAECEE; box-shadow: 0 1px 3px rgba(0,0,0,0.02); height: 110px; }
    .kpi-title { font-size: 12px; color: #7F8C8D; margin-bottom: 8px; display: flex; justify-content: space-between; }
    .kpi-value { font-size: 28px; font-weight: 800; color: #2C3E50; margin-bottom: 4px; line-height: 1.1; }
    .kpi-desc { font-size: 11px; color: #A6ACAF; }
    .section-header { font-size: 11px; font-weight: 700; color: #7F8C8D; letter-spacing: 1px; margin-top: 30px; margin-bottom: 5px; text-transform: uppercase; }
    .section-title { font-size: 18px; font-weight: 700; color: #2C3E50; margin-bottom: 15px; }
    .qa-brief-card { background-color: #1A362D; color: white; padding: 25px; border-radius: 8px; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .qa-title { font-size: 11px; font-weight: bold; color: #A3E4D7; letter-spacing: 1px; margin-bottom: 8px; }
    .qa-main-text { font-size: 18px; font-weight: 700; margin-bottom: 15px; }
    .qa-content { font-size: 13px; line-height: 1.7; color: #E8F8F5; margin-bottom: 15px; }
    .qa-highlight { font-weight: 700; color: #FFFFFF; border-bottom: 1px solid #A3E4D7; padding-bottom: 2px; }
    .signal-box { background-color: #FDFAF2; border: 1px solid #F6DDCC; padding: 18px; border-radius: 8px; display: flex; align-items: center; gap: 15px; margin-bottom: 10px; }
    .signal-icon { background-color: #FDEBD0; padding: 10px; border-radius: 8px; color: #D68910; }
    .ai-summary-card { background-color: #FFFFFF; padding: 15px 20px; margin-bottom: 10px; border-radius: 4px; border: 1px solid #EAECEE; border-left: 4px solid #45B39D; }
    .ai-summary-title { font-weight: 700; color: #1A362D; margin-bottom: 5px; font-size: 14px; }
    .ai-summary-text { font-size: 13px; color: #5D6D7E; line-height: 1.5; }
    .pl-card { background-color: #F5EEF8; border: 1px solid #EBDEF0; padding: 20px; border-radius: 8px; text-align: center; }
    .pl-title { color: #5B2C6F; font-size: 13px; font-weight: bold; margin-bottom: 10px; }
    .pl-value { color: #7D3C98; font-size: 32px; font-weight: 800; }
    .crash-card { background-color: #FDFEFE; padding: 18px; margin-bottom: 12px; border-radius: 4px; border: 1px solid #E5E7E9; border-left: 4px solid #8E44AD; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    .crash-title { font-weight: 800; color: #4A235A; font-size: 14px; margin-bottom: 8px; }
    .crash-meta { font-size: 11px; color: #5B2C6F; margin-right: 8px; background-color: #F4ECF7; padding: 3px 6px; border-radius: 4px; font-weight: 600; display: inline-block; margin-bottom: 4px;}
    .crash-text { font-size: 13px; color: #2C3E50; line-height: 1.5; margin-top: 8px; }
    .complaint-card { background-color: #FDEDEC; padding: 18px; margin-bottom: 12px; border-radius: 4px; border: 1px solid #FADBD8; border-left: 4px solid #E74C3C; }
    .disabled-card { background-color: #EBEDEF; border: 1px dashed #BDC3C7; padding: 30px; text-align: center; border-radius: 8px; color: #7F8C8D; margin-top: 15px; }
    div[data-testid="stButton"] button { padding: 4px 10px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. UI 및 차트 최적화 헬퍼 함수
# ==========================================
def apply_chart_style(fig, height=300):
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=height, 
                      margin=dict(l=0, r=10, t=20, b=0), xaxis=dict(showgrid=False, title=None), yaxis=dict(title=None))
    return fig

def render_list_card(title, meta_list, text, url_info=None):
    meta_html = "".join([f'<span class="crash-meta">{m}</span>' for m in meta_list])
    st.markdown(f'''
        <div class="crash-card">
            <div class="crash-title">{title}</div>
            <div>{meta_html}</div>
            <div class="crash-text"><b>상세 내용:</b> {text}</div>
        </div>
    ''', unsafe_allow_html=True)
    if url_info:
        st.caption(url_info['text'])
        st.code(url_info['url'], language="text")

# ==========================================
# 3. 데이터 로딩 (가상 컴플레인 + NHTSA 실시간 리콜 API)
# ==========================================
DATA_MIN_DATE, DATA_MAX_DATE = date(2013, 1, 1), date(2026, 9, 8)

@st.cache_data
def load_nhtsa_complaints():
    np.random.seed(42)
    n_records = 5000
    dates = pd.to_datetime(np.random.choice(pd.date_range('2013-01-01', '2026-09-08'), n_records))
    brands = np.random.choice(['NEXEN', 'HANKOOK', 'KUMHO', 'MICHELIN', 'GOODYEAR', 'CONTINENTAL'], n_records, p=[0.18, 0.22, 0.18, 0.22, 0.10, 0.10])
    symptoms = np.random.choice(['Tread Separation', 'Sidewall Blowout', 'Vibration/Noise', 'Rapid Wear', 'Air Loss/Cracking'], n_records)
    veh_makes = np.random.choice(['HYUNDAI', 'KIA', 'FORD', 'CHEVROLET', 'TOYOTA', 'RAM'], n_records)
    veh_models = np.random.choice(['SONATA', 'K5', 'F-150', 'SILVERADO', 'CAMRY', 'RAM 3500'], n_records)
    vehicles = [f"{m} {md}" for m, md in zip(veh_makes, veh_models)]
    tire_models = {
        'NEXEN': ['N Priz AH8', 'Roadian HTX', 'N Fera AU7', 'Aria AH7', 'Winguard'],
        'HANKOOK': ['Dynapro HT', 'Kinergy PT', 'Ventus S1', 'Optimo H724', 'Vantra LT'],
        'KUMHO': ['Crugen HP71', 'Solus TA31', 'Ecsta PS31', 'Road Venture', 'HA32'],
        'MICHELIN': ['Defender LTX', 'Premier A/S', 'Pilot Sport 4', 'CrossClimate2', 'Energy Saver'],
        'GOODYEAR': ['Wrangler SR-A', 'Assurance MaxLife', 'Eagle F1', 'Fortera HL', 'Ultragrip'],
        'CONTINENTAL': ['CrossContact LX', 'ProContact TX', 'ExtremeContact', 'PureContact', 'VancoFourSeason']
    }
    models = [np.random.choice(tire_models[b]) for b in brands]
    sizes = np.random.choice(['225/55R17', '235/45R18', '245/40R19', '215/55R17', '275/40R20'], n_records)
    states = np.random.choice(['CA', 'TX', 'FL', 'NY', 'PA', 'OH', 'GA', 'NC'], n_records)
    crashes = np.random.choice([0, 1], n_records, p=[0.92, 0.08])
    texts = [f"주행 중 {s} 증상 발생. (차종: {v}, 타이어: {b} {m}, 규격: {sz}, 지역: {stt})" for s, v, b, m, sz, stt in zip(symptoms, vehicles, brands, models, sizes, states)]
    
    return pd.DataFrame({'Date': dates, 'Year': dates.year, 'Brand': brands, 'Symptom': symptoms, 
                         'Vehicle_Make': veh_makes, 'Vehicle': vehicles, 'Model': models, 
                         'Size': sizes, 'State': states, 'Crash': crashes, 'Complaint_Text': texts})

@st.cache_data(ttl=3600)
def load_real_nhtsa_recalls():
    url = "https://datahub.transportation.gov/api/views/mu99-t4jn/rows.csv?accessType=DOWNLOAD"
    try:
        df = pd.read_csv(url, low_memory=False)
        df.columns = [str(c).strip().upper().replace(' ', '_') for c in df.columns]
        if 'RECALL_TYPE' in df.columns:
            df = df[df['RECALL_TYPE'].str.upper().str.contains('TIRE', na=False)]
        if 'REPORT_RECEIVED_DATE' in df.columns:
            df['Report_Received_Date'] = pd.to_datetime(df['REPORT_RECEIVED_DATE'], errors='coerce')
            df['Year'] = df['Report_Received_Date'].dt.year
        df.rename(columns={'MANUFACTURER': 'Manufacturer', 'COMPONENT': 'Component', 'NHTSA_CAMPAIGN_NUMBER': 'Campaign_Number', 'SUBJECT': 'Subject', 'SUMMARY': 'Summary'}, inplace=True)
        df['Summary'] = df['Summary'].fillna("상세 내용 없음")
        df['Subject'] = df['Subject'].fillna("제목 없음")
        return df
    except Exception as e:
        np.random.seed(100)
        n_recalls = 500
        dates = pd.to_datetime(np.random.choice(pd.date_range('2013-01-01', '2026-09-08'), n_recalls))
        brands = np.random.choice(['NEXEN TIRE AMERICA INC', 'HANKOOK TIRE', 'KUMHO TIRE USA', 'MICHELIN NORTH AMERICA', 'GOODYEAR TIRE', 'CONTINENTAL TIRE'], n_recalls)
        components = np.random.choice(['TIRES:TREAD/BELT', 'TIRES:SIDEWALL', 'TIRES:VALVE', 'TIRES:PRESSURE MONITORING'], n_recalls)
        campaign_nums = [f"{str(y)[-2:]}T{np.random.randint(100, 999):03d}" for y in dates.year]
        return pd.DataFrame({'Report_Received_Date': dates, 'Year': dates.year, 'Manufacturer': brands, 
                             'Component': components, 'Campaign_Number': campaign_nums, 
                             'Subject': "Tire Defect Detected", 'Summary': "Synthetic fallback data due to API connection error."})

df_comp = load_nhtsa_complaints()
df_recall = load_real_nhtsa_recalls()

# ==========================================
# 4. Session State 초기화 및 사이드바 제어
# ==========================================
for key, default in zip(['filter_brands', 'filter_start_date', 'filter_end_date'], [['NEXEN'], DATA_MIN_DATE, DATA_MAX_DATE]):
    if key not in st.session_state: st.session_state[key] = default

def reset_filters():
    st.session_state.filter_brands, st.session_state.filter_start_date, st.session_state.filter_end_date = ['NEXEN'], DATA_MIN_DATE, DATA_MAX_DATE
def set_nexen_focus(): st.session_state.filter_brands = ['NEXEN']
def set_all_brands(): st.session_state.filter_brands = list(df_comp['Brand'].unique())

with st.sidebar:
    col_hdr1, col_hdr2 = st.columns([3, 1])
    col_hdr1.markdown("**🔍 탐색 필터**")
    col_hdr2.button("초기화", on_click=reset_filters, use_container_width=True)
    st.markdown("---")
    
    col_btn1, col_btn2 = st.columns(2)
    col_btn1.button("NEXEN 중심", on_click=set_nexen_focus, use_container_width=True)
    col_btn2.button("전체 브랜드", on_click=set_all_brands, use_container_width=True)
    
    with st.form("filter_form"):
        all_brand_options = list(df_comp['Brand'].unique())
        selected_brands = st.multiselect("타이어 브랜드 (BRAND)", options=all_brand_options, default=st.session_state.filter_brands)
        selected_models = st.multiselect("타이어 모델 (MODEL)", options=sorted(list(df_comp['Model'].unique())))
        selected_sizes = st.multiselect("타이어 규격 (SIZE)", options=sorted(list(df_comp['Size'].unique())))
        selected_makes = st.multiselect("차량 제조사 (MAKE)", options=sorted(list(df_comp['Vehicle_Make'].unique())))
        selected_vehicles = st.multiselect("차종 (VEHICLE)", options=sorted(list(df_comp['Vehicle'].unique())))
        selected_symptoms = st.multiselect("결함 증상 (SYMPTOM)", options=sorted(list(df_comp['Symptom'].unique())))
        selected_states = st.multiselect("발생 지역 (STATE)", options=sorted(list(df_comp['State'].unique())))
        crash_option = st.radio("사고/피해 여부", ["전체", "사고 동반건만 보기"], index=0)
        
        st.markdown("---")
        st.markdown("**📅 기간 기준**")
        sel_start = st.date_input("시작일", value=st.session_state.filter_start_date, min_value=DATA_MIN_DATE, max_value=DATA_MAX_DATE)
        sel_end = st.date_input("종료일", value=st.session_state.filter_end_date, min_value=DATA_MIN_DATE, max_value=DATA_MAX_DATE)
        
        if st.form_submit_button("필터 적용하기", type="primary", use_container_width=True):
            st.session_state.filter_brands = selected_brands if selected_brands else all_brand_options
            st.session_state.filter_start_date, st.session_state.filter_end_date = sel_start, sel_end

# ==========================================
# 5. 데이터 동적 필터링 적용
# ==========================================
mask_comp = (df_comp['Date'].dt.date >= st.session_state.filter_start_date) & (df_comp['Date'].dt.date <= st.session_state.filter_end_date)
if st.session_state.filter_brands: mask_comp &= (df_comp['Brand'].isin(st.session_state.filter_brands))
if selected_models: mask_comp &= (df_comp['Model'].isin(selected_models))
if selected_sizes: mask_comp &= (df_comp['Size'].isin(selected_sizes))
if selected_makes: mask_comp &= (df_comp['Vehicle_Make'].isin(selected_makes))
if selected_vehicles: mask_comp &= (df_comp['Vehicle'].isin(selected_vehicles))
if selected_symptoms: mask_comp &= (df_comp['Symptom'].isin(selected_symptoms))
if selected_states: mask_comp &= (df_comp['State'].isin(selected_states))
if crash_option == "사고 동반건만 보기": mask_comp &= (df_comp['Crash'] == 1)

df_filtered = df_comp[mask_comp]

mask_recall = (df_recall['Report_Received_Date'].dt.date >= st.session_state.filter_start_date) & (df_recall['Report_Received_Date'].dt.date <= st.session_state.filter_end_date)
if st.session_state.filter_brands and "전체" not in st.session_state.filter_brands:
    brand_conds = [df_recall['Manufacturer'].str.upper().str.contains(b.upper(), na=False) for b in st.session_state.filter_brands]
    mask_recall &= np.logical_or.reduce(brand_conds)
df_recalls_filtered = df_recall[mask_recall]

target_year = st.session_state.filter_end_date.year
is_multi_brand = len(st.session_state.filter_brands) > 1 or st.session_state.filter_brands[0] == '전체'
color_opt = 'Brand' if is_multi_brand else None

if df_filtered.empty:
    st.warning("선택한 필터 조건에 해당하는 데이터가 존재하지 않습니다.")
    st.stop()

# ==========================================
# 6. 메인 헤더 & KPI 카드
# ==========================================
st.markdown('<div class="top-category">NHTSA / TIRE QUALITY MONITOR</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">작은 신호에서, 품질의 다음을.</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">NHTSA 타이어 결함 신고 통합 모니터링 시스템</div>', unsafe_allow_html=True)

brand_str = ", ".join(st.session_state.filter_brands) if len(st.session_state.filter_brands) <= 3 else f"{st.session_state.filter_brands[0]} 외 {len(st.session_state.filter_brands)-1}개"
st.markdown(f'''
    <div class="badge-container">
        <span class="status-badge">● 데이터 정상 연결</span>
        <span class="filter-badge">선택 브랜드: {brand_str}</span>
        <span class="filter-badge">조회 기간: {st.session_state.filter_start_date} ~ {st.session_state.filter_end_date}</span>
    </div>
''', unsafe_allow_html=True)

col_k1, col_k2, col_k3, col_k4 = st.columns(4)
col_k1.markdown(f'<div class="kpi-card"><div class="kpi-title">총 접수 건수 📄</div><div class="kpi-value">{len(df_filtered):,}</div><div class="kpi-desc">선택 기간 내 집계 건수</div></div>', unsafe_allow_html=True)
col_k2.markdown(f'<div class="kpi-card"><div class="kpi-title">최근 180일 접수 ↗</div><div class="kpi-value">{len(df_filtered[df_filtered["Date"].dt.date >= st.session_state.filter_end_date - timedelta(days=180)]):,}</div><div class="kpi-desc">최신 동향 모니터링</div></div>', unsafe_allow_html=True)
col_k3.markdown(f'<div class="kpi-card"><div class="kpi-title">타이어 리콜 (PL) ⚠</div><div class="kpi-value">{len(df_recalls_filtered):,}</div><div class="kpi-desc">NHTSA 실시간 리콜 연동</div></div>', unsafe_allow_html=True)
col_k4.markdown(f'<div class="kpi-card"><div class="kpi-title">영향 차종 수 🚗</div><div class="kpi-value">{df_filtered["Vehicle"].nunique():,}</div><div class="kpi-desc">신고된 고유 차종</div></div>', unsafe_allow_html=True)

# ==========================================
# 7. 신고건수 추이 & 요약 브리핑
# ==========================================
col_m1, col_m2 = st.columns([2.3, 1])
with col_m1:
    st.markdown('<div class="section-header">COMPLAINT TREND</div><div class="section-title">연도별 신고 건수 추이</div>', unsafe_allow_html=True)
    trend_data = df_filtered.groupby('Year').size().reset_index(name='Count').sort_values('Year')
    trend_data['Year'] = trend_data['Year'].astype(str)
    fig_trend = px.bar(trend_data, x='Year', y='Count', text='Count')
    fig_trend.update_traces(marker_color='#719A7E', width=0.4, textposition='outside')
    fig_trend = apply_chart_style(fig_trend)
    fig_trend.update_xaxes(type='category')
    st.plotly_chart(fig_trend, use_container_width=True)

with col_m2:
    st.markdown('<div class="section-header">&nbsp;</div>', unsafe_allow_html=True)
    top_sym = df_filtered['Symptom'].value_counts().idxmax()
    top_v = df_filtered['Vehicle'].value_counts().idxmax()
    st.markdown(f'''
        <div class="qa-brief-card">
            <div class="qa-title">✨ SUMMARY BRIEF</div>
            <div class="qa-main-text">조회 조건 요약</div>
            <div class="qa-content">선택 조건 내 총 <span class="qa-highlight">{len(df_filtered):,}건</span>의 컴플레인 확인.<br><br>최다 결함 패턴: <span class="qa-highlight">{top_sym}</span><br><br>최다 신고 차종: <span class="qa-highlight">{top_v}</span></div>
        </div>
    ''', unsafe_allow_html=True)

# ==========================================
# 8. 패턴 현황, 지역별 현황 (3열 한줄 배치) 및 드릴다운 통합 섹션
# ==========================================
st.markdown('<div class="section-header">PATTERN & REGION EXPLORER</div>', unsafe_allow_html=True)

col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    st.markdown('<div style="font-weight:bold; font-size:16px; margin-bottom:10px;">지역별 발생 현황 (State)</div>', unsafe_allow_html=True)
    top_states = df_filtered['State'].value_counts().head(10).index
    state_agg = df_filtered[df_filtered['State'].isin(top_states)].groupby(['State', 'Brand']).size().reset_index(name='Count')
    state_agg = state_agg.merge(state_agg.groupby('State')['Count'].sum().reset_index(name='Total'), on='State')
    fig_state = px.bar(state_agg, x='Count', y='State', color=color_opt, orientation='h', text='Count')
    if not is_multi_brand: fig_state.update_traces(marker_color='#5D6D7E')
    fig_state.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(apply_chart_style(fig_state, height=320), use_container_width=True)

with col_p2:
    st.markdown('<div style="font-weight:bold; font-size:16px; margin-bottom:10px;">[NEXEN 단독] 상위 10개 패턴</div>', unsafe_allow_html=True)
    df_nx_pat = df_filtered[df_filtered['Brand'] == 'NEXEN']
    if not df_nx_pat.empty:
        pat_nx = df_nx_pat.groupby(['Model', 'Symptom']).size().reset_index(name='Count')
        pat_nx['Pattern'] = pat_nx['Model'] + " (" + pat_nx['Symptom'] + ")"
        fig_nx = px.bar(pat_nx.nlargest(10, 'Count'), x='Count', y='Pattern', orientation='h', text='Count')
        fig_nx.update_traces(marker_color='#45B39D', width=0.4, textposition='outside')
        fig_nx.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(apply_chart_style(fig_nx, height=320), use_container_width=True)
    else: st.info("조건에 해당하는 NEXEN 데이터가 없습니다.")

with col_p3:
    st.markdown('<div style="font-weight:bold; font-size:16px; margin-bottom:10px;">[타사 포함 전체] 상위 10개 패턴</div>', unsafe_allow_html=True)
    other_brands_selected = any(b != 'NEXEN' for b in st.session_state.filter_brands)
    if not other_brands_selected:
        st.markdown('''
            <div class="disabled-card" style="padding: 100px 20px; margin-top: 0; height: 320px;">
                <div style="margin-bottom: 10px;">💡 <b>타사 브랜드 미지정</b></div>
                <div style="font-size: 13px;">탐색 필터에서 타사 브랜드를 추가 선택하시면<br>비교 차트가 활성화됩니다.</div>
            </div>
        ''', unsafe_allow_html=True)
    else:
        pat_all = df_filtered.groupby(['Brand', 'Model', 'Symptom']).size().reset_index(name='Count')
        pat_all['Pattern'] = pat_all['Brand'] + " " + pat_all['Model'] + " (" + pat_all['Symptom'] + ")"
        fig_all = px.bar(pat_all.nlargest(10, 'Count'), x='Count', y='Pattern', color=color_opt, orientation='h', text='Count')
        if not is_multi_brand: fig_all.update_traces(marker_color='#5D6D7E')
        fig_all.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(apply_chart_style(fig_all, height=320), use_container_width=True)

# 결함 증상 심층 분석 박스 (드릴다운 연동)
st.markdown('<div style="padding: 20px; background-color: #FFFFFF; border: 1px solid #EAECEE; border-radius: 8px; margin-top: 15px;">', unsafe_allow_html=True)
st.markdown('<div class="section-title" style="margin-bottom:15px;">🔎 주요 결함·증상 키워드별 발생 현황 및 상세 분석 (Drill-down)</div>', unsafe_allow_html=True)

col_d1, col_d2 = st.columns([1, 1.2])
with col_d1:
    sym_agg = df_filtered.groupby(['Symptom', 'Brand']).size().reset_index(name='Count')
    sym_agg = sym_agg.merge(sym_agg.groupby('Symptom')['Count'].sum().reset_index(name='Total'), on='Symptom')
    fig_sym = px.bar(sym_agg, x='Count', y='Symptom', color=color_opt, orientation='h', text='Count')
    if not is_multi_brand: fig_sym.update_traces(marker_color='#5D6D7E') 
    fig_sym.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(apply_chart_style(fig_sym, height=300), use_container_width=True)

with col_d2:
    sym_list = df_filtered['Symptom'].value_counts().index.tolist()
    selected_sym = st.selectbox("👉 상세 패턴 리스트를 확인할 결함 증상을 선택하세요:", options=sym_list)
    
    if selected_sym:
        sym_df = df_filtered[df_filtered['Symptom'] == selected_sym]
        pat_sym = sym_df.groupby(['Brand', 'Model']).size().reset_index(name='Count')
        pat_sym['Pattern'] = pat_sym['Brand'] + " " + pat_sym['Model']
        top_pat_sym = pat_sym.nlargest(5, 'Count') # 공간 확보를 위해 Top 5
        
        fig_sd = px.bar(top_pat_sym, x='Count', y='Pattern', orientation='h', text='Count')
        fig_sd.update_traces(marker_color='#E67E22', width=0.4, textposition='outside')
        fig_sd.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(apply_chart_style(fig_sd, height=200), use_container_width=True)
        
        with st.expander(f"'{selected_sym}' 최근 주요 발생 사례 (5건)"):
            for _, r in sym_df.sort_values('Date', ascending=False).head(5).iterrows():
                st.markdown(f"<div style='font-size:12px; margin-bottom:8px; border-bottom:1px solid #eee; padding-bottom:5px;'><b>[{r['Brand']}] {r['Model']}</b> ({r['Date'].strftime('%Y-%m-%d')}, 지역: {r['State']})<br>{r['Complaint_Text']}</div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 9. NEXEN 전용 신호 감지 & AI 요약
# ==========================================
st.markdown('<div class="section-header" style="margin-top: 40px;">NEXEN DEEP DIVE</div>', unsafe_allow_html=True)
st.markdown(f'<div class="section-title">NEXEN: {target_year}년 컴플레인 이상 신호 및 AI 분석</div>', unsafe_allow_html=True)

df_nx_target = df_comp[(df_comp['Brand'] == 'NEXEN') & (df_comp['Year'] == target_year)]
df_nx_prev = df_comp[(df_comp['Brand'] == 'NEXEN') & (df_comp['Year'].isin([target_year-1, target_year-2, target_year-3]))]

if not df_nx_target.empty:
    tc, pc = df_nx_target['Symptom'].value_counts(), df_nx_prev['Symptom'].value_counts() / 3.0 
    max_increase, spike_sym, t_val, p_val, is_new = -1, "특이사항 없음", 0, 0, False
    
    for sym in tc.index:
        c_tc, c_pc = tc[sym], pc.get(sym, 0)
        diff = c_tc - c_pc
        if c_pc == 0 and c_tc > 0:
            if diff > max_increase or not is_new: max_increase, spike_sym, t_val, p_val, is_new = diff, sym, c_tc, c_pc, True
        elif not is_new and diff > max_increase:
            max_increase, spike_sym, t_val, p_val = diff, sym, c_tc, c_pc
            
    if is_new:
        msg = f"{target_year}년 들어 NEXEN 타이어의 <b>{spike_sym}</b> 컴플레인이 과거 3년간 접수 이력이 <b>전혀 없었으나</b> 신규로 <b>{t_val}건</b> 발생했습니다."
        st.markdown(f'<div class="signal-box"><div class="signal-icon">⚠️</div><div><div style="font-weight: bold; color: #9C640C; font-size: 15px;">[패턴 감지] {target_year}년 {spike_sym} 집중 발생 <span style="border: 1px solid #E6B0AA; color: #C0392B; font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-left: 10px;">🚨 신규 급증</span></div><div style="color: #A6ACAF; font-size: 12px; margin-top: 5px;">{msg}</div></div></div>', unsafe_allow_html=True)
    elif max_increase > 0:
        st.markdown(f'<div class="signal-box"><div class="signal-icon">⚠️</div><div><div style="font-weight: bold; color: #9C640C; font-size: 15px;">[패턴 감지] {target_year}년 {spike_sym} 집중 발생 <span style="border: 1px solid #E59866; color: #D35400; font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-left: 10px;">증가 ↗</span></div><div style="color: #A6ACAF; font-size: 12px; margin-top: 5px;">과거 3년 평균({p_val:.1f}건) 대비 <b>{t_val}건</b>으로 증가했습니다.</div></div></div>', unsafe_allow_html=True)

    st.markdown(f'<div style="margin-top:20px; font-weight:bold; font-size: 15px; color:#2C3E50;">▶ {target_year}년 발생 전체 사례 목록</div>', unsafe_allow_html=True)
    cases_nx = df_nx_target.sort_values('Date', ascending=False)
    
    def render_ai_card(r):
        st.markdown(f'<div class="ai-summary-card"><div class="ai-summary-title">사례. {r["State"]} 지역 - {r["Symptom"]} ({r["Date"].strftime("%Y-%m-%d")})</div><div class="ai-summary-text">{r["Complaint_Text"]}</div></div>', unsafe_allow_html=True)
    
    for _, r in cases_nx.head(3).iterrows(): render_ai_card(r)
    if len(cases_nx) > 3:
        with st.expander(f"더보기 ({len(cases_nx)-3}건 전체 목록)"):
            with st.container(height=350):
                for _, r in cases_nx.iloc[3:].iterrows(): render_ai_card(r)
else: st.info(f"NEXEN 브랜드의 {target_year}년 데이터가 없어 분석을 생략합니다.")

# ==========================================
# 10. 전체 조회기간 사고/피해 동반 (Complaints) 상세 보고서
# ==========================================
st.markdown('<div class="section-header" style="margin-top: 40px;">ALL-TIME CRASH REPORT LOGS</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">📝 전체 조회기간 사고·피해 동반 (Complaints) 상세 보고서</div>', unsafe_allow_html=True)

all_crash_df = df_filtered[df_filtered['Crash'] == 1].sort_values('Date', ascending=False)

def render_complaint_crash(r):
    meta = [f"📅 {r['Date'].strftime('%Y-%m-%d')}", f"📍 {r['State']}", f"🛞 {r['Model']} ({r['Size']})"]
    render_list_card(f"[{r['Brand']}] {r['Vehicle']} - {r['Symptom']} 사고 발생", meta, r['Complaint_Text'])

if all_crash_df.empty:
    st.info("전체 기간 내 사고/피해 동반 신고 건이 없습니다.")
else:
    for _, r in all_crash_df.head(3).iterrows(): render_complaint_crash(r)
    if len(all_crash_df) > 3:
        with st.expander(f"더보기 ({len(all_crash_df)-3}건 전체 목록)"):
            with st.container(height=400):
                for _, r in all_crash_df.iloc[3:].iterrows(): render_complaint_crash(r)

# ==========================================
# 11. 넥센 & 경쟁사 비교 분석 섹션
# ==========================================
st.markdown('<div class="section-header" style="margin-top: 40px;">COMPETITOR BENCHMARK</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">⚖️ NEXEN vs 경쟁사 비교 분석 보고서</div>', unsafe_allow_html=True)

active_brands = list(df_filtered['Brand'].unique())
if 'NEXEN' in active_brands: active_brands.remove('NEXEN'); active_brands.insert(0, 'NEXEN')

if not is_multi_brand:
    st.markdown('<div class="disabled-card"><h4>💡 브랜드 비교 분석 비활성화 상태</h4><p>좌측 탐색 필터에서 <b>전체 브랜드</b>를 누르거나 <b>2개 이상</b> 복수 선택 시 자동 활성화됩니다.</p></div>', unsafe_allow_html=True)
else:
    st.markdown("#### 1. 선택 브랜드별 접수 현황 요약")
    b_sum = df_filtered.groupby('Brand').agg(총컴플레인=('Brand', 'count'), 최다증상=('Symptom', lambda x: x.value_counts().idxmax())).reset_index()
    recall_cnts = [len(df_recalls_filtered[df_recalls_filtered['Manufacturer'].str.upper().str.contains(b.upper(), na=False)]) for b in b_sum['Brand']]
    b_sum.insert(2, '타이어 리콜(PL)', recall_cnts)
    b_sum = b_sum.sort_values('총컴플레인', ascending=False).reset_index(drop=True)
    b_sum.index = np.arange(1, len(b_sum) + 1); b_sum.index.name = 'No.'
    st.dataframe(b_sum, use_container_width=True)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("#### 2. 연도별 추이 비교")
        y_b_df = df_filtered.groupby(['Year', 'Brand']).size().reset_index(name='Count').sort_values('Year')
        y_b_df['Year'] = y_b_df['Year'].astype(str)
        fig_comp_trend = px.line(y_b_df, x='Year', y='Count', color='Brand', markers=True)
        st.plotly_chart(apply_chart_style(fig_comp_trend, 300), use_container_width=True)
    with col_c2:
        st.markdown("#### 3. Tire Fail Type 현황")
        fig_fail = px.bar(df_filtered.groupby(['Symptom', 'Brand']).size().reset_index(name='Count'), x='Symptom', y='Count', color='Brand', barmode='group')
        st.plotly_chart(apply_chart_style(fig_fail, 300), use_container_width=True)
    
    st.markdown("#### 4. 각 브랜드별 상위 10개 모델 (클릭하여 증상 상세 보기)")
    for i in range(0, len(active_brands), 3):
        cols = st.columns(3)
        for idx, b_name in enumerate(active_brands[i:i+3]):
            with cols[idx]:
                st.markdown(f"**[{b_name}] Top 모델**")
                b_m_df = df_filtered[df_filtered['Brand'] == b_name].groupby('Model').size().reset_index(name='Count').sort_values('Count', ascending=False).head(10)
                for _, row in b_m_df.iterrows():
                    with st.expander(f"{row['Model']} ({row['Count']}건)"):
                        sym_counts = df_filtered[(df_filtered['Brand'] == b_name) & (df_filtered['Model'] == row['Model'])]['Symptom'].value_counts().reset_index()
                        sym_counts.columns = ['결함 증상', '발생 건수']
                        st.dataframe(sym_counts, hide_index=True, use_container_width=True)

st.markdown("<br><div style='text-align:center; font-size:11px; color:#A6ACAF;'>본 대시보드는 NHTSA 실시간 데이터 및 조건부 가상 데이터를 복합적으로 활용하여 구성되었습니다.</div>", unsafe_allow_html=True)
