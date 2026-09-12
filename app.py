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
    
    .pl-card { background-color: #FDEDEC; border: 1px solid #FADBD8; padding: 20px; border-radius: 8px; text-align: center; }
    .pl-title { color: #922B21; font-size: 13px; font-weight: bold; margin-bottom: 10px; }
    .pl-value { color: #C0392B; font-size: 32px; font-weight: 800; }
    
    .crash-card { background-color: #FDEDEC; padding: 18px; margin-bottom: 12px; border-radius: 4px; border: 1px solid #FADBD8; border-left: 4px solid #E74C3C; }
    .crash-title { font-weight: 800; color: #922B21; font-size: 14px; margin-bottom: 8px; }
    .crash-meta { font-size: 11px; color: #922B21; margin-right: 8px; background-color: #F5B7B1; padding: 3px 6px; border-radius: 4px; font-weight: 600; display: inline-block; margin-bottom: 4px;}
    .crash-text { font-size: 13px; color: #641E16; line-height: 1.5; margin-top: 8px; }
    
    .disabled-card { background-color: #EBEDEF; border: 1px dashed #BDC3C7; padding: 30px; text-align: center; border-radius: 8px; color: #7F8C8D; margin-top: 15px; }
    
    div[data-testid="stButton"] button { padding: 4px 10px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터 생성
# ==========================================
DATA_MIN_DATE = date(2013, 1, 1)
DATA_MAX_DATE = date(2026, 9, 8)

@st.cache_data
def load_nhtsa_data():
    np.random.seed(42)
    n_records = 5000
    
    dates = pd.to_datetime(np.random.choice(pd.date_range('2013-01-01', '2026-09-08'), n_records))
    brands = np.random.choice(['NEXEN', 'HANKOOK', 'KUMHO', 'MICHELIN', 'GOODYEAR', 'CONTINENTAL'], n_records, p=[0.18, 0.22, 0.18, 0.22, 0.10, 0.10])
    symptoms = np.random.choice(['Tread Separation', 'Sidewall Blowout', 'Vibration/Noise', 'Rapid Wear', 'Air Loss/Cracking'], n_records)
    veh_makes = np.random.choice(['HYUNDAI', 'KIA', 'FORD', 'CHEVROLET', 'TOYOTA', 'RAM'], n_records)
    veh_models = np.random.choice(['SONATA', 'K5', 'F-150', 'SILVERADO', 'CAMRY', 'RAM 3500'], n_records)
    vehicles = [f"{m} {md}" for m, md in zip(veh_makes, veh_models)]
    prod_years = np.random.choice(range(2010, 2026), n_records)
    
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
    speeds = np.random.choice(['60-70 mph', '70-80 mph', '50-60 mph', 'Under 50 mph', 'Over 80 mph'], n_records)
    crashes = np.random.choice([0, 1], n_records, p=[0.92, 0.08])
    
    texts = [f"주행 중 {s} 증상으로 차량 통제 불능 발생. (차종: {v}, 타이어: {b} {m}, 규격: {sz}, 발생지역: {stt})" 
             for s, v, b, m, sz, stt in zip(symptoms, vehicles, brands, models, sizes, states)]
    
    df = pd.DataFrame({
        'Date': dates,
        'Year': dates.year,
        'Brand': brands,
        'Symptom': symptoms,
        'Vehicle_Make': veh_makes,
        'Vehicle_Model': veh_models,
        'Vehicle': vehicles,
        'Prod_Year': prod_years,
        'Model': models,
        'Size': sizes,
        'State': states,
        'Speed': speeds,
        'Crash': crashes,
        'Complaint_Text': texts
    })
    return df

df_base = load_nhtsa_data()

# ==========================================
# 3. Session State 초기화 및 사이드바 버튼
# ==========================================
if 'filter_brands' not in st.session_state: st.session_state.filter_brands = ['NEXEN']
if 'filter_start_date' not in st.session_state: st.session_state.filter_start_date = DATA_MIN_DATE
if 'filter_end_date' not in st.session_state: st.session_state.filter_end_date = DATA_MAX_DATE

def reset_filters():
    st.session_state.filter_brands = ['NEXEN']
    st.session_state.filter_start_date = DATA_MIN_DATE
    st.session_state.filter_end_date = DATA_MAX_DATE

def set_nexen_focus(): st.session_state.filter_brands = ['NEXEN']
def set_all_brands(): st.session_state.filter_brands = list(df_base['Brand'].unique())

# ==========================================
# 4. 사이드바 구성 
# ==========================================
with st.sidebar:
    col_hdr1, col_hdr2 = st.columns([3, 1])
    col_hdr1.markdown("**🔍 탐색 필터**")
    col_hdr2.button("초기화", on_click=reset_filters, use_container_width=True)
    st.markdown("---")
    
    col_btn1, col_btn2 = st.columns(2)
    col_btn1.button("NEXEN 중심", on_click=set_nexen_focus, use_container_width=True)
    col_btn2.button("전체 브랜드", on_click=set_all_brands, use_container_width=True)
    
    with st.form("filter_form"):
        all_brand_options = list(df_base['Brand'].unique())
        selected_brands = st.multiselect("타이어 브랜드 (BRAND)", options=all_brand_options, default=st.session_state.filter_brands)
        selected_models = st.multiselect("타이어 모델 (MODEL)", options=sorted(list(df_base['Model'].unique())))
        selected_sizes = st.multiselect("타이어 규격 (SIZE)", options=sorted(list(df_base['Size'].unique())))
        selected_makes = st.multiselect("차량 제조사 (MAKE)", options=sorted(list(df_base['Vehicle_Make'].unique())))
        selected_vehicles = st.multiselect("차종 (VEHICLE)", options=sorted(list(df_base['Vehicle'].unique())))
        selected_symptoms = st.multiselect("결함 증상 (SYMPTOM)", options=sorted(list(df_base['Symptom'].unique())))
        selected_states = st.multiselect("발생 지역 (STATE)", options=sorted(list(df_base['State'].unique())))
        crash_option = st.radio("사고/피해 여부", ["전체", "사고 동반건만 보기"], index=0)
        
        st.markdown("---")
        st.markdown("**📅 기간 기준**")
        sel_start = st.date_input("시작일", value=st.session_state.filter_start_date, min_value=DATA_MIN_DATE, max_value=DATA_MAX_DATE)
        sel_end = st.date_input("종료일", value=st.session_state.filter_end_date, min_value=DATA_MIN_DATE, max_value=DATA_MAX_DATE)
        
        submit_btn = st.form_submit_button("필터 적용하기", type="primary", use_container_width=True)
        if submit_btn:
            st.session_state.filter_brands = selected_brands if selected_brands else all_brand_options
            st.session_state.filter_start_date = sel_start
            st.session_state.filter_end_date = sel_end

# ==========================================
# 5. 데이터 동적 필터링 적용
# ==========================================
mask = (df_base['Date'].dt.date >= st.session_state.filter_start_date) & (df_base['Date'].dt.date <= st.session_state.filter_end_date)
if st.session_state.filter_brands: mask &= (df_base['Brand'].isin(st.session_state.filter_brands))
if selected_models: mask &= (df_base['Model'].isin(selected_models))
if selected_sizes: mask &= (df_base['Size'].isin(selected_sizes))
if selected_makes: mask &= (df_base['Vehicle_Make'].isin(selected_makes))
if selected_vehicles: mask &= (df_base['Vehicle'].isin(selected_vehicles))
if selected_symptoms: mask &= (df_base['Symptom'].isin(selected_symptoms))
if selected_states: mask &= (df_base['State'].isin(selected_states))
if crash_option == "사고 동반건만 보기": mask &= (df_base['Crash'] == 1)

df_filtered = df_base[mask]
target_year = st.session_state.filter_end_date.year

if df_filtered.empty:
    st.warning("선택한 필터 조건에 해당하는 데이터가 존재하지 않습니다. 기간이나 조건을 변경해주세요.")
    st.stop()

is_multi_brand = len(st.session_state.filter_brands) > 1 or st.session_state.filter_brands[0] == '전체'
color_opt = 'Brand' if is_multi_brand else None

# ==========================================
# 6. 메인 헤더 & KPI 카드
# ==========================================
st.markdown('<div class="top-category">NHTSA / TIRE QUALITY MONITOR</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">작은 신호에서, 품질의 다음을.</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">NHTSA 타이어 결함 신고 통합 모니터링 시스템</div>', unsafe_allow_html=True)

selected_brands_str = ", ".join(st.session_state.filter_brands) if len(st.session_state.filter_brands) <= 3 else f"{st.session_state.filter_brands[0]} 외 {len(st.session_state.filter_brands)-1}개"

st.markdown(f'''
    <div class="badge-container">
        <span class="status-badge">● 데이터 정상 연결</span>
        <span class="filter-badge">선택 브랜드: {selected_brands_str}</span>
        <span class="filter-badge">조회 기간: {st.session_state.filter_start_date} ~ {st.session_state.filter_end_date}</span>
    </div>
''', unsafe_allow_html=True)

total_cnt = len(df_filtered)
recent_180_cnt = len(df_filtered[df_filtered['Date'].dt.date >= st.session_state.filter_end_date - timedelta(days=180)])
crash_cnt = df_filtered['Crash'].sum()
unique_veh = df_filtered['Vehicle'].nunique()

col_k1, col_k2, col_k3, col_k4 = st.columns(4)
col_k1.markdown(f'<div class="kpi-card"><div class="kpi-title">총 접수 건수 📄</div><div class="kpi-value">{total_cnt:,}</div><div class="kpi-desc">선택 기간 내 집계 건수</div></div>', unsafe_allow_html=True)
col_k2.markdown(f'<div class="kpi-card"><div class="kpi-title">최근 180일 접수 ↗</div><div class="kpi-value">{recent_180_cnt:,}</div><div class="kpi-desc">최신 동향 모니터링</div></div>', unsafe_allow_html=True)
col_k3.markdown(f'<div class="kpi-card"><div class="kpi-title">사고·피해 동반 ⚠</div><div class="kpi-value">{crash_cnt:,}</div><div class="kpi-desc">인명/물적 피해 연관</div></div>', unsafe_allow_html=True)
col_k4.markdown(f'<div class="kpi-card"><div class="kpi-title">영향 차종 수 🚗</div><div class="kpi-value">{unique_veh:,}</div><div class="kpi-desc">신고된 고유 차종</div></div>', unsafe_allow_html=True)

# ==========================================
# 7. 신고건수 추이 & 요약 브리핑
# ==========================================
col_m1, col_m2 = st.columns([2.3, 1])
with col_m1:
    st.markdown('<div class="section-header">COMPLAINT TREND</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">연도별 신고 건수 추이</div>', unsafe_allow_html=True)
    trend_data = df_filtered.groupby('Year').size().reset_index(name='Count').sort_values('Year')
    trend_data['Year'] = trend_data['Year'].astype(str)
    fig_trend = px.bar(trend_data, x='Year', y='Count', text='Count')
    fig_trend.update_traces(marker_color='#719A7E', width=0.4, textposition='outside')
    fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(l=0, r=0, t=20, b=0), xaxis=dict(type='category', title=None), yaxis=dict(title=None))
    st.plotly_chart(fig_trend, use_container_width=True)

with col_m2:
    st.markdown('<div class="section-header">&nbsp;</div>', unsafe_allow_html=True)
    top_sym = df_filtered['Symptom'].value_counts().idxmax()
    top_sym_c = df_filtered['Symptom'].value_counts().max()
    top_v = df_filtered['Vehicle'].value_counts().idxmax()
    top_v_c = df_filtered['Vehicle'].value_counts().max()
    st.markdown(f'''
        <div class="qa-brief-card">
            <div class="qa-title">✨ SUMMARY BRIEF</div>
            <div class="qa-main-text">조회 조건 요약</div>
            <div class="qa-content">
                선택 조건 내 총 <span class="qa-highlight">{total_cnt:,}건</span>의 컴플레인이 확인되었습니다.<br><br>
                최다 발생 결함 패턴은 <span class="qa-highlight">{top_sym} ({top_sym_c}건)</span>입니다.<br><br>
                최다 신고 차종은 <span class="qa-highlight">{top_v} ({top_v_c}건)</span>입니다.
            </div>
        </div>
    ''', unsafe_allow_html=True)

# ==========================================
# 8. 모델별 패턴 현황 (NEXEN vs 전체 분리) 및 지역별 발생현황
# ==========================================
st.markdown('<div class="section-header">PATTERN & REGION EXPLORER</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">타이어 모델별 상위 10개 패턴 현황</div>', unsafe_allow_html=True)

col_pat1, col_pat2 = st.columns(2)

with col_pat1:
    st.markdown('**[NEXEN 단독] 상위 10개 패턴**')
    df_nx_pat = df_filtered[df_filtered['Brand'] == 'NEXEN']
    if not df_nx_pat.empty:
        pat_nx = df_nx_pat.groupby(['Model', 'Symptom']).size().reset_index(name='Count')
        pat_nx['Pattern'] = pat_nx['Model'] + " (" + pat_nx['Symptom'] + ")"
        top10_nx = pat_nx.sort_values(by='Count', ascending=False).head(10).sort_values(by='Count', ascending=True)
        fig_nx = px.bar(top10_nx, x='Count', y='Pattern', orientation='h', text='Count')
        fig_nx.update_traces(marker_color='#45B39D', width=0.4, textposition='outside')
        fig_nx.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=320, margin=dict(l=0, r=20, t=10, b=0), xaxis=dict(showgrid=False, title=None), yaxis=dict(title=None))
        st.plotly_chart(fig_nx, use_container_width=True)
    else:
        st.info("조건에 해당하는 NEXEN 데이터가 없습니다.")

with col_pat2:
    st.markdown('**[타사 포함 전체] 상위 10개 패턴**')
    pat_all = df_filtered.groupby(['Brand', 'Model', 'Symptom']).size().reset_index(name='Count')
    pat_all['Pattern'] = pat_all['Brand'] + " " + pat_all['Model'] + " (" + pat_all['Symptom'] + ")"
    top10_all = pat_all.sort_values(by='Count', ascending=False).head(10).sort_values(by='Count', ascending=True)
    fig_all = px.bar(top10_all, x='Count', y='Pattern', color=color_opt, orientation='h', text='Count')
    if not is_multi_brand: fig_all.update_traces(marker_color='#5D6D7E')
    fig_all.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=320, margin=dict(l=0, r=20, t=10, b=0), xaxis=dict(showgrid=False, title=None), yaxis=dict(title=None))
    st.plotly_chart(fig_all, use_container_width=True)

st.markdown('<div class="section-title" style="margin-top:20px;">지역별 발생 현황 (State)</div>', unsafe_allow_html=True)
col_st1, col_st2 = st.columns(2)
with col_st1:
    top10_states = df_filtered['State'].value_counts().head(10).index
    state_df = df_filtered[df_filtered['State'].isin(top10_states)]
    state_agg = state_df.groupby(['State', 'Brand']).size().reset_index(name='Count')
    state_totals = state_df.groupby('State').size().reset_index(name='Total')
    state_agg = state_agg.merge(state_totals, on='State').sort_values('Total', ascending=True)
    fig_state = px.bar(state_agg, x='Count', y='State', color=color_opt, orientation='h', text='Count')
    if not is_multi_brand: fig_state.update_traces(marker_color='#5D6D7E')
    fig_state.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=320, margin=dict(l=0, r=20, t=10, b=0), xaxis=dict(showgrid=False, title=None), yaxis=dict(title=None))
    st.plotly_chart(fig_state, use_container_width=True)


# ==========================================
# 9. NEXEN 전용 신호 감지 & AI 요약
# ==========================================
st.markdown('<div class="section-header">NEXEN DEEP DIVE</div>', unsafe_allow_html=True)
st.markdown(f'<div class="section-title">NEXEN: {target_year}년 컴플레인 이상 신호 및 AI 분석</div>', unsafe_allow_html=True)

df_nexen = df_base[df_base['Brand'] == 'NEXEN']
df_nx_target = df_nexen[df_nexen['Year'] == target_year]
df_nx_prev = df_nexen[df_nexen['Year'].isin([target_year-1, target_year-2, target_year-3])]

if not df_nx_target.empty:
    target_counts = df_nx_target['Symptom'].value_counts()
    prev_counts = df_nx_prev['Symptom'].value_counts() / 3.0 
    
    max_increase = -1
    spike_symptom = "특이사항 없음"
    t_cnt, p_cnt = 0, 0
    is_new_anomaly = False 
    
    for sym in target_counts.index:
        tc = target_counts[sym]
        pc = prev_counts.get(sym, 0)
        diff = tc - pc
        
        # 신규 발생(0건->N건)을 최우선 심각 패턴으로 간주
        if pc == 0 and tc > 0:
            if diff > max_increase or not is_new_anomaly:
                max_increase = diff
                spike_symptom = sym
                t_cnt = tc
                p_cnt = pc
                is_new_anomaly = True
        elif not is_new_anomaly and diff > max_increase:
            max_increase = diff
            spike_symptom = sym
            t_cnt = tc
            p_cnt = pc
            
    if is_new_anomaly:
        badge_text = "🚨 신규 급증"
        badge_color = "#C0392B"
        badge_border = "#E6B0AA"
        msg = f"{target_year}년 들어 NEXEN 타이어의 <b>{spike_symptom}</b> 컴플레인이 과거 3년간 접수 이력이 <b>전혀 없었으나</b> 신규로 <b>{t_cnt}건</b> 발생하여 즉각적인 점검이 필요합니다."
    elif max_increase > 0:
        badge_text = "증가 ↗"
        badge_color = "#D35400"
        badge_border = "#E59866"
        msg = f"{target_year}년 NEXEN 타이어 <b>{spike_symptom}</b> 컴플레인이 과거 3년 평균({p_cnt:.1f}건) 대비 <b>{t_cnt}건</b>으로 증가 추세를 보입니다."
    else:
        badge_text = "안정적 ↘"
        badge_color = "#2E86C1"
        badge_border = "#85C1E9"
        msg = f"{target_year}년 주요 컴플레인({spike_symptom}) 발생 빈도가 과거 대비 안정적인 수준을 유지하고 있습니다."
    
    st.markdown(f'''
        <div class="signal-box">
            <div class="signal-icon">⚠️</div>
            <div>
                <div style="font-weight: bold; color: #9C640C; font-size: 15px;">
                    [패턴 감지] {target_year}년 '{spike_symptom}' 집중 발생 
                    <span style="border: 1px solid {badge_border}; color: {badge_color}; font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-left: 10px;">{badge_text}</span>
                </div>
                <div style="color: #A6ACAF; font-size: 12px; margin-top: 5px;">{msg}</div>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    st.markdown(f'<div style="margin-top:20px; font-weight:bold; font-size: 15px; color:#2C3E50;">▶ {target_year}년 발생 전체 사례 목록</div>', unsafe_allow_html=True)
    cases_nx = df_nx_target.sort_values('Date', ascending=False)
    
    # 1~3건 기본 노출, 그 이상은 Expander
    for idx, r in cases_nx.head(3).iterrows():
        st.markdown(f'''
            <div class="ai-summary-card">
                <div class="ai-summary-title">사례. {r['State']} 지역 - {r['Symptom']} ({r['Date'].strftime('%Y-%m-%d')})</div>
                <div class="ai-summary-text">{r['Complaint_Text']}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    if len(cases_nx) > 3:
        with st.expander(f"더보기 ({len(cases_nx)-3}건 전체 목록)"):
            with st.container(height=350):
                for idx, r in cases_nx.iloc[3:].iterrows():
                    st.markdown(f'''
                        <div class="ai-summary-card">
                            <div class="ai-summary-title">사례. {r['State']} 지역 - {r['Symptom']} ({r['Date'].strftime('%Y-%m-%d')})</div>
                            <div class="ai-summary-text">{r['Complaint_Text']}</div>
                        </div>
                    ''', unsafe_allow_html=True)
else:
    st.info(f"NEXEN 브랜드의 {target_year}년 데이터가 없어 분석을 생략합니다.")


# ==========================================
# 10. 해당년도 PL 상세 보고서 (Expandable UI)
# ==========================================
def draw_pl_card(r):
    st.markdown(f'''
        <div class="crash-card">
            <div class="crash-title">[{r['Brand']}] {r['Vehicle']} - {r['Symptom']} 사고 접수</div>
            <div>
                <span class="crash-meta">📅 {r['Date'].strftime('%Y-%m-%d')}</span>
                <span class="crash-meta">📍 {r['State']}</span>
                <span class="crash-meta">⏱ {r['Speed']}</span>
                <span class="crash-meta">🛞 {r['Model']} ({r['Size']})</span>
            </div>
            <div class="crash-text"><b>상세 내용:</b> {r['Complaint_Text']}</div>
        </div>
    ''', unsafe_allow_html=True)
    if r['Brand'] == 'NEXEN':
        mock_pl_no = f"PL-{r['Date'].strftime('%Y%m%d')}-{np.random.randint(1000,9999)}"
        st.caption(f"NEXEN PL No: {mock_pl_no} (클릭하여 URL 복사)")
        st.code(f"https://www.nhtsa.gov/report/{mock_pl_no}", language="text")

st.markdown('<div class="section-header" style="margin-top: 40px;">PRODUCT LIABILITY (PL) STATUS</div>', unsafe_allow_html=True)
st.markdown(f'<div class="section-title">🚨 {target_year}년 타이어 PL (사고/피해 동반) 현황 및 상세 보고서</div>', unsafe_allow_html=True)

df_pl_target = df_filtered[(df_filtered['Year'] == target_year) & (df_filtered['Crash'] == 1)]

if df_pl_target.empty:
    st.success(f"{target_year}년 선택 필터 내에 접수된 타이어 결함 사고/피해(PL) 건수가 없습니다.")
else:
    col_pl1, col_pl2, col_pl3 = st.columns([1, 2, 2])
    with col_pl1:
        st.markdown(f'''
        <div class="pl-card" style="height:100%; display:flex; flex-direction:column; justify-content:center;">
            <div class="pl-title">{target_year}년 총 PL 접수</div>
            <div class="pl-value">{len(df_pl_target)}<span style="font-size:16px; color:#E74C3C;"> 건</span></div>
            <div style="font-size:12px; color:#A6ACAF; margin-top:5px;">선택 조건 내 사고 동반</div>
        </div>
        ''', unsafe_allow_html=True)
    with col_pl2:
        fig_pl_b = px.pie(df_pl_target.groupby('Brand').size().reset_index(name='Count'), names='Brand', values='Count', hole=0.4, title="브랜드별 PL 비중")
        fig_pl_b.update_layout(height=220, margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pl_b, use_container_width=True)
    with col_pl3:
        fig_pl_s = px.bar(df_pl_target.groupby('Symptom').size().reset_index(name='Count'), x='Count', y='Symptom', orientation='h', title="원인(증상)별 PL 건수")
        fig_pl_s.update_traces(marker_color='#E74C3C', width=0.4)
        fig_pl_s.update_layout(height=220, margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis=dict(title=None))
        st.plotly_chart(fig_pl_s, use_container_width=True)
    
    st.markdown("#### 📑 해당년도 PL 상세 보고서")
    df_pl_sorted = df_pl_target.sort_values('Date', ascending=False)
    
    for _, r in df_pl_sorted.head(3).iterrows():
        draw_pl_card(r)
        
    if len(df_pl_sorted) > 3:
        with st.expander(f"더보기 ({len(df_pl_sorted)-3}건 전체 목록)"):
            with st.container(height=400):
                for _, r in df_pl_sorted.iloc[3:].iterrows():
                    draw_pl_card(r)


# ==========================================
# 11. 전체 조회기간 사고·피해 동반 상세 보고서
# ==========================================
st.markdown('<div class="section-header" style="margin-top: 40px;">ALL-TIME CRASH REPORT LOGS</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">📝 전체 조회기간 사고·피해 동반 상세 보고서</div>', unsafe_allow_html=True)

all_crash_df = df_filtered[df_filtered['Crash'] == 1].sort_values('Date', ascending=False)

if all_crash_df.empty:
    st.info("선택 조건 내 전체 기간에 사고/피해 동반 신고 건이 없습니다.")
else:
    for _, r in all_crash_df.head(3).iterrows():
        draw_pl_card(r)
        
    if len(all_crash_df) > 3:
        with st.expander(f"더보기 ({len(all_crash_df)-3}건 전체 목록)"):
            with st.container(height=400):
                for _, r in all_crash_df.iloc[3:].iterrows():
                    draw_pl_card(r)


# ==========================================
# 12. 넥센 & 경쟁사 비교 분석 섹션
# ==========================================
st.markdown('<div class="section-header" style="margin-top: 40px;">COMPETITOR BENCHMARK</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">⚖️ NEXEN vs 경쟁사 비교 분석 보고서</div>', unsafe_allow_html=True)

active_brands = list(df_filtered['Brand'].unique())

if not is_multi_brand:
    st.markdown('''
        <div class="disabled-card">
            <h4>💡 브랜드 비교 분석 비활성화 상태</h4>
            <p>좌측 탐색 필터에서 <b>'전체 브랜드'</b>를 누르거나 <b>2개 이상의 브랜드</b>를 복수 선택하시면 경쟁사 비교 보고서가 자동 활성화됩니다.</p>
        </div>
    ''', unsafe_allow_html=True)
else:
    st.success(f"비교 분석 활성화됨 (비교 대상 브랜드: {', '.join(active_brands)})")
    
    st.markdown("#### 1. 선택 브랜드별 접수 현황 요약")
    b_summary = df_filtered.groupby('Brand').agg(총접수건수=('Brand', 'count'), 사고동반건수=('Crash', 'sum'), 최다결함증상=('Symptom', lambda x: x.value_counts().idxmax())).reset_index()
    # 총 접수건수 내림차순 정렬 및 No. 1부터 인덱싱
    b_summary = b_summary.sort_values('총접수건수', ascending=False).reset_index(drop=True)
    b_summary.index = np.arange(1, len(b_summary) + 1)
    b_summary.index.name = 'No.'
    st.dataframe(b_summary, use_container_width=True)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("#### 2. 연도별 추이 비교")
        y_b_df = df_filtered.groupby(['Year', 'Brand']).size().reset_index(name='Count').sort_values('Year')
        y_b_df['Year'] = y_b_df['Year'].astype(str)
        fig_comp_trend = px.line(y_b_df, x='Year', y='Count', color='Brand', markers=True)
        fig_comp_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=300, xaxis=dict(type='category', title=None), yaxis=dict(title=None))
        st.plotly_chart(fig_comp_trend, use_container_width=True)
    with col_c2:
        st.markdown("#### 3. Tire Fail Type 현황")
        fail_b_df = df_filtered.groupby(['Symptom', 'Brand']).size().reset_index(name='Count')
        fig_fail = px.bar(fail_b_df, x='Symptom', y='Count', color='Brand', barmode='group')
        fig_fail.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=300, xaxis=dict(title=None), yaxis=dict(title=None))
        st.plotly_chart(fig_fail, use_container_width=True)
    
    st.markdown("#### 4. 각 브랜드별 상위 10개 모델 (클릭하여 증상 상세 보기)")
    
    # 선택된 모든 브랜드에 대해 3열씩 묶어서 출력
    for i in range(0, len(active_brands), 3):
        chunk = active_brands[i:i+3]
        cols = st.columns(3)
        for idx, b_name in enumerate(chunk):
            with cols[idx]:
                st.markdown(f"**[{b_name}] Top 모델**")
                b_m_df = df_filtered[df_filtered['Brand'] == b_name].groupby('Model').size().reset_index(name='Count').sort_values('Count', ascending=False).head(10)
                
                # 모델을 Expander로 생성 (드릴다운)
                for _, row in b_m_df.iterrows():
                    m_name = row['Model']
                    m_cnt = row['Count']
                    with st.expander(f"{m_name} ({m_cnt}건)"):
                        sym_counts = df_filtered[(df_filtered['Brand'] == b_name) & (df_filtered['Model'] == m_name)]['Symptom'].value_counts().reset_index()
                        sym_counts.columns = ['결함 증상', '발생 건수']
                        st.dataframe(sym_counts, hide_index=True, use_container_width=True)

st.markdown("<br><div style='text-align:center; font-size:11px; color:#A6ACAF;'>본 대시보드의 데이터는 지정된 조회 기간에 맞춰 실시간 연동되어 표출됩니다.</div>", unsafe_allow_html=True)
