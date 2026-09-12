import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# ==========================================
# 1. 페이지 기본 설정 및 통합 커스텀 CSS
# ==========================================
st.set_page_config(page_title="NHTSA / TIRE QUALITY MONITOR", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* 폰트 및 기본 배경 */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #F8F9F9; }
    
    /* 상단 헤더 */
    .top-category { font-size: 12px; font-weight: 700; color: #7F8C8D; letter-spacing: 1px; margin-bottom: 5px; }
    .main-title { font-size: 36px; font-weight: 800; color: #1E272E; margin-bottom: 5px; }
    .sub-title { font-size: 15px; color: #7F8C8D; margin-bottom: 25px; }
    
    /* 뱃지 */
    .badge-container { display: flex; gap: 10px; margin-bottom: 20px; }
    .status-badge { background-color: #EAFAF1; color: #27AE60; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .filter-badge { background-color: #F2F3F4; color: #5D6D7E; padding: 4px 10px; border-radius: 4px; font-size: 12px; border: 1px solid #E5E8E8; }
    
    /* KPI 카드 */
    .kpi-card { background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #EAECEE; box-shadow: 0 1px 3px rgba(0,0,0,0.02); height: 120px; }
    .kpi-title { font-size: 13px; color: #7F8C8D; margin-bottom: 10px; display: flex; justify-content: space-between; }
    .kpi-value { font-size: 32px; font-weight: 800; color: #2C3E50; margin-bottom: 5px; line-height: 1.2; }
    .kpi-desc { font-size: 12px; color: #A6ACAF; }
    
    /* 섹션 타이틀 */
    .section-header { font-size: 11px; font-weight: 700; color: #7F8C8D; letter-spacing: 1px; margin-top: 30px; margin-bottom: 5px; text-transform: uppercase; }
    .section-title { font-size: 18px; font-weight: 700; color: #2C3E50; margin-bottom: 15px; }
    
    /* QA Brief 카드 (다크 그린) */
    .qa-brief-card { background-color: #1A362D; color: white; padding: 30px; border-radius: 8px; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .qa-title { font-size: 12px; font-weight: bold; color: #A3E4D7; letter-spacing: 1px; margin-bottom: 10px; }
    .qa-main-text { font-size: 20px; font-weight: 700; margin-bottom: 20px; }
    .qa-content { font-size: 14px; line-height: 1.8; color: #E8F8F5; margin-bottom: 20px; }
    .qa-highlight { font-weight: 700; color: #FFFFFF; border-bottom: 1px solid #A3E4D7; padding-bottom: 2px; }
    .qa-button { background-color: transparent; color: white; border: 1px solid #45B39D; padding: 8px 15px; border-radius: 4px; font-size: 13px; width: 100%; text-align: center; cursor: pointer; }
    
    /* 신호 알림 박스 */
    .signal-box { background-color: #FDFAF2; border: 1px solid #F6DDCC; padding: 20px; border-radius: 8px; display: flex; align-items: center; gap: 15px; margin-bottom: 10px; }
    .signal-icon { background-color: #FDEBD0; padding: 10px; border-radius: 8px; color: #D68910; }
    
    /* AI 요약 카드 (이미지 1 내용 + 이미지 2 테마 적용) */
    .ai-summary-card { background-color: #FFFFFF; border-left: 4px solid #45B39D; padding: 15px 20px; margin-bottom: 10px; border-radius: 4px; border-top: 1px solid #EAECEE; border-right: 1px solid #EAECEE; border-bottom: 1px solid #EAECEE; }
    .ai-summary-title { font-weight: 700; color: #1A362D; margin-bottom: 5px; font-size: 14px; }
    .ai-summary-text { font-size: 13px; color: #5D6D7E; line-height: 1.5; }
    
    /* 커스텀 테이블 (이미지 1 정량비교용) */
    .custom-table th { background-color: #1A362D !important; color: white !important; font-weight: normal; text-align: center; }
    .custom-table td { text-align: center; color: #2C3E50; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. 사이드바 (탐색 필터) - 이미지 2 기준
# ==========================================
with st.sidebar:
    st.markdown("**탐색 필터** <span style='float:right; font-size:12px; color:gray; cursor:pointer;'>초기화</span>", unsafe_allow_html=True)
    st.markdown("---")
    col_btn1, col_btn2 = st.columns(2)
    col_btn1.button("NEXEN 중심", type="primary", use_container_width=True)
    col_btn2.button("전체 브랜드", use_container_width=True)
    
    st.text_input("타이어 관련 키워드", placeholder="NEXEN, sidewall, DOT...")
    st.selectbox("타이어 브랜드", ["NEXEN (80)"])
    st.selectbox("브랜드 판별 근거", ["등록 브랜드 + 원문 언급"])
    st.selectbox("차량 브랜드", ["전체 차량 브랜드"])
    st.selectbox("차종", ["전체 차종"])
    
    st.markdown("---")
    st.markdown("**기간 기준**")
    st.date_input("시작일", value=date(2020, 1, 1))
    st.date_input("종료일", value=date(2026, 9, 8))


# ==========================================
# 3. 메인 헤더 및 KPI 영역 (이미지 2 기준)
# ==========================================
st.markdown('<div class="top-category">NHTSA / TIRE QUALITY MONITOR</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">작은 신호에서, 품질의 다음을.</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">타이어 관련 신고를 연결하고, 확인이 필요한 패턴을 찾아보세요.</div>', unsafe_allow_html=True)
st.markdown('''
    <div class="badge-container">
        <span class="status-badge">● 공식 데이터 확보</span>
        <span class="filter-badge">조회 기준 2026-09-11</span>
        <span class="filter-badge">최종 접수 2026-09-08</span>
    </div>
''', unsafe_allow_html=True)

st.markdown('<div class="section-title">NEXEN 모니터링</div>', unsafe_allow_html=True)
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
with col_kpi1:
    st.markdown('<div class="kpi-card"><div class="kpi-title">필터에 해당하는 신고 📄</div><div class="kpi-value">80</div><div class="kpi-desc">ODI 신고번호 기준 - 중복 제거</div></div>', unsafe_allow_html=True)
with col_kpi2:
    st.markdown('<div class="kpi-card"><div class="kpi-title">최근 180일 접수 ↗</div><div class="kpi-value">7</div><div class="kpi-desc">직전 180일 7건 +0%</div></div>', unsafe_allow_html=True)
with col_kpi3:
    st.markdown('<div class="kpi-card"><div class="kpi-title">사고·피해 동반 신고 ⚠</div><div class="kpi-value">1</div><div class="kpi-desc">사고 1 - 부상 신고 0건</div></div>', unsafe_allow_html=True)
with col_kpi4:
    st.markdown('<div class="kpi-card"><div class="kpi-title">등록 차종 🚗</div><div class="kpi-value">34</div><div class="kpi-desc">차량 정보 미등록 1건 별도</div></div>', unsafe_allow_html=True)


# ==========================================
# 4. 트렌드 차트 & QA Brief
# ==========================================
col_mid1, col_mid2 = st.columns([2.3, 1])

with col_mid1:
    st.markdown('<div class="section-header">COMPLAINT TREND</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">신고 건수 추이</div>', unsafe_allow_html=True)
    trend_data = pd.DataFrame({'Year': ['2020', '2021', '2022', '2023', '2024', '2025', '2026*'], 'Count': [11, 17, 12, 7, 11, 14, 8]})
    fig_trend = px.bar(trend_data, x='Year', y='Count', text='Count')
    fig_trend.update_traces(marker_color='#719A7E', width=0.4, textposition='outside', textfont=dict(color='gray'))
    fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=320, margin=dict(l=0, r=0, t=20, b=0), xaxis_title=None, yaxis_title=None, yaxis=dict(showgrid=True, gridcolor='#F2F3F4'), xaxis=dict(showgrid=False))
    st.plotly_chart(fig_trend, use_container_width=True)

with col_mid2:
    st.markdown('<div class="section-header">&nbsp;</div>', unsafe_allow_html=True)
    st.markdown('''
        <div class="qa-brief-card">
            <div class="qa-title">✨ YOUR QA BRIEF</div>
            <div class="qa-main-text">현재 필터 요약</div>
            <div class="qa-content">
                NEXEN 관련 신고 <span class="qa-highlight">80건</span>이 현재 조건에 해당합니다.<br><br>
                가장 많이 포착된 증상은 <span class="qa-highlight">트레드-벨트 분리 (29건)</span>입니다.<br><br>
                등록 차종 중 <span class="qa-highlight">RAM 3500 (29건)</span>이 가장 많습니다.
            </div>
            <div class="qa-button">📋 요약 복사</div>
        </div>
    ''', unsafe_allow_html=True)


# ==========================================
# 5. 신호 감지 & AI 원문 요약 (이미지 1 + 2 통합)
# ==========================================
st.markdown('<div class="section-header">FROM PATTERNS TO QUESTIONS</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">어떤 신호를 먼저 살펴볼까요?</div>', unsafe_allow_html=True)

st.markdown('''
    <div class="signal-box">
        <div class="signal-icon">📈</div>
        <div>
            <div style="font-weight: bold; color: #9C640C; font-size: 15px;">균열-드라이 로트 - 증가 후보 <span style="border: 1px solid #E59866; color: #D35400; font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-left: 10px;">신규 ↗</span></div>
            <div style="color: #A6ACAF; font-size: 12px; margin-top: 5px;">최근 180일 3건 / 이전 0건</div>
        </div>
    </div>
''', unsafe_allow_html=True)

# 이미지 1의 AI 요약 내용을 이미지 2의 세련된 디자인으로 통합
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
<div class="ai-summary-card">
    <div class="ai-summary-title">사례 3. 특정 속도 구간에서의 이상 진동 (Vibration/Noise)</div>
    <div class="ai-summary-text">50~60mph 구간에서 차량 전체에 심한 진동 발생. 딜러샵 점검 결과 타이어 내부 구조 변형(벨트 분리 의심)으로 판정받아 4본 모두 조기 교체 진행.</div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# 6. 다차원 탐색 (가로 바 차트 2행 3열 그리드 - 이미지 1,2 통합)
# ==========================================
def draw_horizontal_bar(df, x_col, y_col):
    fig = px.bar(df, x=x_col, y=y_col, orientation='h', text=x_col)
    fig.update_traces(marker_color='#719A7E', width=0.2, textposition='outside', textfont=dict(color='#2C3E50', size=11))
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=250, margin=dict(l=0, r=20, t=10, b=0),
                      xaxis=dict(showgrid=False, showticklabels=False, title=None, range=[0, df[x_col].max()*1.3]),
                      yaxis=dict(showgrid=False, title=None, categoryorder='total ascending', tickfont=dict(color='#5D6D7E', size=11)))
    return fig

# 첫 번째 행: 증상, 차종, 타이어 모델 (이미지 1+2)
col_b1, col_b2, col_b3 = st.columns(3)
with col_b1:
    st.markdown('<div class="section-header">SYMPTOM EXPLORER</div><div class="section-title">주요 결함-증상</div>', unsafe_allow_html=True)
    sym_df = pd.DataFrame({'Item': ['트레드 분리', '진동-밸런스', '파열 Blowout', '변형-부풀음', '균열 Cracking'][::-1], 'Count': [29, 25, 18, 11, 7][::-1]})
    st.plotly_chart(draw_horizontal_bar(sym_df, 'Count', 'Item'), use_container_width=True)
with col_b2:
    st.markdown('<div class="section-header">VEHICLE EXPLORER</div><div class="section-title">차종별 분포</div>', unsafe_allow_html=True)
    veh_df = pd.DataFrame({'Item': ['RAM 3500', 'Hyundai Sonata', 'JEEP WRANGLER', 'Ford F-150', 'Kia K5'][::-1], 'Count': [29, 25, 8, 6, 5][::-1]})
    st.plotly_chart(draw_horizontal_bar(veh_df, 'Count', 'Item'), use_container_width=True)
with col_b3:
    st.markdown('<div class="section-header">MODEL EXPLORER</div><div class="section-title">타이어 모델 분포</div>', unsafe_allow_html=True)
    mod_df = pd.DataFrame({'Item': ['N Priz AH8', 'Roadian HTX', 'N Fera AU7', 'Aria AH7', 'Winguard'][::-1], 'Count': [32, 18, 14, 9, 7][::-1]})
    st.plotly_chart(draw_horizontal_bar(mod_df, 'Count', 'Item'), use_container_width=True)

# 두 번째 행: 규격, 발생지역, 속도 (이미지 1 상세 내용)
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    st.markdown('<div class="section-header">SIZE EXPLORER</div><div class="section-title">주요 규격 분포</div>', unsafe_allow_html=True)
    size_df = pd.DataFrame({'Item': ['225/55R17', '235/45R18', '245/40R19', '215/55R17', '275/40R20'][::-1], 'Count': [24, 19, 15, 12, 10][::-1]})
    st.plotly_chart(draw_horizontal_bar(size_df, 'Count', 'Item'), use_container_width=True)
with col_c2:
    st.markdown('<div class="section-header">STATE EXPLORER</div><div class="section-title">발생 지역(State)</div>', unsafe_allow_html=True)
    state_df = pd.DataFrame({'Item': ['CA (캘리포니아)', 'TX (텍사스)', 'FL (플로리다)', 'NY (뉴욕)', 'PA (펜실베니아)'][::-1], 'Count': [22, 18, 15, 10, 8][::-1]})
    st.plotly_chart(draw_horizontal_bar(state_df, 'Count', 'Item'), use_container_width=True)
with col_c3:
    st.markdown('<div class="section-header">SPEED EXPLORER</div><div class="section-title">주행 속도</div>', unsafe_allow_html=True)
    speed_df = pd.DataFrame({'Item': ['60-70 mph', '70-80 mph', '50-60 mph', 'Under 50 mph', 'Over 80 mph'][::-1], 'Count': [35, 20, 15, 6, 4][::-1]})
    st.plotly_chart(draw_horizontal_bar(speed_df, 'Count', 'Item'), use_container_width=True)


# ==========================================
# 7. 글로벌 경쟁사 상세 비교 (이미지 1 표 데이터 편입)
# ==========================================
st.markdown('<div class="section-header">DEEP DIVE: COMPETITOR ANALYSIS</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">글로벌 4대 브랜드 상세 정량 비교</div>', unsafe_allow_html=True)

compare_data = pd.DataFrame({
    '평가 항목': ['누적 접수 건수', '사망/부상 비율(심각도)', '최다 불만 유형 (1순위)', '추돌/화재 사고 건수', '종합 경쟁력 지수'],
    'NEXEN': ['182건', '1.6%', 'Tread Separation', '0건', '우수 (A)'],
    'HANKOOK': ['454건', '2.1%', 'Sidewall Blowout', '2건', '양호 (B+)'],
    'KUMHO': ['421건', '2.5%', 'Vibration/Noise', '1건', '양호 (B+)'],
    'MICHELIN': ['2,168건', '1.2%', 'Rapid Wear', '5건', '우수 (A)']
})

# 표를 HTML로 렌더링하여 스타일 적용
html_table = compare_data.to_html(classes='custom-table', index=False, border=0)
st.markdown(html_table, unsafe_allow_html=True)

st.markdown("<br><div style='text-align:center; font-size:11px; color:#A6ACAF;'>신고 건수는 판매량·장착 대수로 보정된 불량률이 아닙니다. 타이어의 결함이나 사고 원인을 확정하지 않습니다.</div>", unsafe_allow_html=True)
