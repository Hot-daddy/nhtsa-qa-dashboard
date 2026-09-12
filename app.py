import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# ==========================================
# 페이지 기본 설정
# ==========================================
st.set_page_config(page_title="NHTSA / TIRE QUALITY MONITOR", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 커스텀 CSS (이미지 테마 및 레이아웃 완벽 재현)
# ==========================================
st.markdown("""
    <style>
    /* 폰트 및 배경 기본 설정 */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #F8F9F9; }
    
    /* 상단 헤더 스타일 */
    .top-category { font-size: 12px; font-weight: 700; color: #7F8C8D; letter-spacing: 1px; margin-bottom: 5px; }
    .main-title { font-size: 36px; font-weight: 800; color: #1E272E; margin-bottom: 5px; }
    .sub-title { font-size: 15px; color: #7F8C8D; margin-bottom: 25px; }
    
    /* 뱃지 스타일 */
    .badge-container { display: flex; gap: 10px; margin-bottom: 20px; }
    .status-badge { background-color: #EAFAF1; color: #27AE60; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    .filter-badge { background-color: #F2F3F4; color: #5D6D7E; padding: 4px 10px; border-radius: 4px; font-size: 12px; border: 1px solid #E5E8E8; }
    
    /* KPI 카드 스타일 */
    .kpi-card { background-color: white; padding: 20px; border-radius: 8px; border: 1px solid #EAECEE; box-shadow: 0 1px 3px rgba(0,0,0,0.02); height: 120px; }
    .kpi-title { font-size: 13px; color: #7F8C8D; margin-bottom: 10px; display: flex; justify-content: space-between; }
    .kpi-value { font-size: 32px; font-weight: 800; color: #2C3E50; margin-bottom: 5px; line-height: 1.2; }
    .kpi-desc { font-size: 12px; color: #A6ACAF; }
    
    /* 섹션 타이틀 */
    .section-header { font-size: 11px; font-weight: 700; color: #7F8C8D; letter-spacing: 1px; margin-top: 30px; margin-bottom: 5px; text-transform: uppercase; }
    .section-title { font-size: 18px; font-weight: 700; color: #2C3E50; margin-bottom: 15px; }
    
    /* QA Brief 카드 (다크 그린 영역) */
    .qa-brief-card { background-color: #1A362D; color: white; padding: 30px; border-radius: 8px; height: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .qa-title { font-size: 12px; font-weight: bold; color: #A3E4D7; letter-spacing: 1px; margin-bottom: 10px; }
    .qa-main-text { font-size: 20px; font-weight: 700; margin-bottom: 20px; }
    .qa-content { font-size: 14px; line-height: 1.8; color: #E8F8F5; margin-bottom: 20px; }
    .qa-highlight { font-weight: 700; color: #FFFFFF; border-bottom: 1px solid #A3E4D7; padding-bottom: 2px; }
    .qa-button { background-color: transparent; color: white; border: 1px solid #45B39D; padding: 8px 15px; border-radius: 4px; font-size: 13px; width: 100%; text-align: center; cursor: pointer; }
    
    /* 신호 알림 박스 */
    .signal-box { background-color: #FDFAF2; border: 1px solid #F6DDCC; padding: 20px; border-radius: 8px; display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }
    .signal-icon { background-color: #FDEBD0; padding: 10px; border-radius: 8px; color: #D68910; }
    .signal-title { font-weight: bold; color: #9C640C; font-size: 15px; }
    .signal-desc { color: #A6ACAF; font-size: 12px; margin-top: 5px; }
    .signal-badge { border: 1px solid #E59866; color: #D35400; font-size: 11px; padding: 2px 8px; border-radius: 12px; margin-left: auto; }
    
    /* 우측 상단 블랙 버튼 */
    .black-btn { background-color: #1A362D; color: white !important; padding: 8px 16px; border-radius: 6px; font-weight: bold; font-size: 14px; text-decoration: none; border: none;}
    
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 1. 사이드바 (탐색 필터)
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
    st.selectbox("등록 제조사", ["전체 등록 제조사"])
    st.selectbox("차량 브랜드", ["전체 차량 브랜드"])
    st.selectbox("차종", ["전체 차종"])
    st.selectbox("차량 연식", ["전체 연식"])
    st.selectbox("주요 증상", ["전체 증상"])
    st.selectbox("신고 유형 / 접수 경로", ["전체 접수 경로"])
    st.selectbox("타이어 관련 선정 근거", ["전체 후보"])
    st.selectbox("사고·피해 신고", ["전체 신고"])
    
    st.markdown("---")
    st.markdown("**기간 기준**")
    st.selectbox("", ["NHTSA 접수일"], label_visibility="collapsed")
    st.date_input("시작일", value=date(2020, 1, 1))
    st.date_input("종료일", value=date(2026, 9, 8))
    
    st.checkbox("관심 신고만 보기", value=False)
    
    st.markdown("---")
    st.markdown("<div style='font-size:11px; color:gray;'>• NHTSA 공개 데이터<br>2020-01-01 — 2026-09-08<br>조회 스냅샷 : 자동 갱신 없음</div>", unsafe_allow_html=True)


# ==========================================
# 2. 메인 헤더 및 타이틀 영역
# ==========================================
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
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
with col_h2:
    st.markdown('<br><button class="black-btn" style="float:right;">🔍 신고 탐색하기</button>', unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 3. NEXEN 모니터링 (KPI 카드)
# ==========================================
st.markdown('<div class="section-title">NEXEN 모니터링</div>', unsafe_allow_html=True)
st.markdown('''
    <div class="badge-container" style="margin-bottom:10px;">
        <span class="filter-badge" style="background:white; color:#1A5276;">브랜드: NEXEN ✕</span>
        <span class="filter-badge" style="background:white;">접수일 2020-01-01 — 2026-09-08</span>
    </div>
''', unsafe_allow_html=True)

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.markdown('''
        <div class="kpi-card">
            <div class="kpi-title">필터에 해당하는 신고 📄</div>
            <div class="kpi-value">80</div>
            <div class="kpi-desc">ODI 신고번호 기준 - 중복 제거</div>
        </div>
    ''', unsafe_allow_html=True)
with col_kpi2:
    st.markdown('''
        <div class="kpi-card">
            <div class="kpi-title">최근 180일 접수 ↗</div>
            <div class="kpi-value">7</div>
            <div class="kpi-desc">직전 180일 7건 +0%</div>
        </div>
    ''', unsafe_allow_html=True)
with col_kpi3:
    st.markdown('''
        <div class="kpi-card">
            <div class="kpi-title">사고·피해 동반 신고 ⚠</div>
            <div class="kpi-value">1</div>
            <div class="kpi-desc">사고 1 - 부상 신고 0건</div>
        </div>
    ''', unsafe_allow_html=True)
with col_kpi4:
    st.markdown('''
        <div class="kpi-card">
            <div class="kpi-title">등록 차종 🚗</div>
            <div class="kpi-value">34</div>
            <div class="kpi-desc">차량 정보 미등록 1건 별도</div>
        </div>
    ''', unsafe_allow_html=True)


# ==========================================
# 4. 신고 건수 추이 차트 & QA Brief
# ==========================================
col_mid1, col_mid2 = st.columns([2.3, 1])

with col_mid1:
    st.markdown('<div class="section-header">COMPLAINT TREND</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">신고 건수 추이</div>', unsafe_allow_html=True)
    
    # 트렌드 차트 데이터 구성 (이미지와 동일한 값)
    trend_data = pd.DataFrame({
        'Year': ['2020', '2021', '2022', '2023', '2024', '2025', '2026*'],
        'Count': [11, 17, 12, 7, 11, 14, 8]
    })
    
    fig_trend = px.bar(trend_data, x='Year', y='Count', text='Count')
    fig_trend.update_traces(marker_color='#719A7E', width=0.4, textposition='outside', textfont=dict(color='gray'))
    fig_trend.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        height=320, margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title=None, yaxis_title=None,
        yaxis=dict(showgrid=True, gridcolor='#F2F3F4', range=[0, 22], dtick=5),
        xaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    st.markdown("<div style='font-size:11px; color:gray;'>* 마지막 구간은 2026-09-08까지 집계합니다. 접수일 기준 - 신고 지연과 최근 구간에 미완료 기간을 고려하세요.</div>", unsafe_allow_html=True)

with col_mid2:
    st.markdown('<div class="section-header">&nbsp;</div>', unsafe_allow_html=True)
    st.markdown('''
        <div class="qa-brief-card">
            <div class="qa-title">✨ YOUR QA BRIEF</div>
            <div class="qa-main-text">현재 필터 요약</div>
            <div class="qa-content">
                NEXEN 관련 신고 <span class="qa-highlight">80건</span>이 현재 조건에 해당합니다.<br><br>
                가장 많이 포착된 증상은 <span class="qa-highlight">트레드-벨트 분리 (29건)</span>입니다.<br><br>
                등록 차종 중 <span class="qa-highlight">RAM 3500 (29건)</span>이 가장 많습니다.<br><br>
                <span style="color:#A3E4D7; font-size:12px;">제품·부품 분류 66건 · 브랜드 원문 언급만 확인된 신고 20건</span>
            </div>
            <div class="qa-button">📋 요약 복사</div>
            <div style="text-align:center; font-size:11px; color:#A3E4D7; margin-top:10px;">공개 신고 탐색용 - 결함 판정 아님</div>
        </div>
    ''', unsafe_allow_html=True)


# ==========================================
# 5. 신호 감지 (FROM PATTERNS TO QUESTIONS)
# ==========================================
st.markdown('<div class="section-header">FROM PATTERNS TO QUESTIONS</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">어떤 신호를 먼저 살펴볼까요?</div>', unsafe_allow_html=True)

st.markdown('''
    <div class="signal-box">
        <div class="signal-icon">📈</div>
        <div>
            <div class="signal-title">균열-드라이 로트 - 증가 후보</div>
            <div class="signal-desc">최근 180일 3건 / 이전 0건</div>
        </div>
        <div class="signal-badge">신규 ↗</div>
    </div>
    <div style="font-size:11px; color:#A6ACAF; margin-bottom: 30px;">비고: 2026 03 13 2026 09 08 ↔ 2025 09 14 2026 03 12 · 3건 이상, +2건 및 +50% 이상 (이전 0건은 신규) · 통계적 이상 판정이 아닌 탐색 규칙</div>
''', unsafe_allow_html=True)


# ==========================================
# 6. 하단 3단 컬럼 차트 (Symptom, Peer, Vehicle)
# ==========================================
col_bot1, col_bot2, col_bot3 = st.columns(3)

# 차트 렌더링을 위한 공통 함수 (얇은 가로 바 차트 구현)
def draw_horizontal_bar(df, x_col, y_col):
    fig = px.bar(df, x=x_col, y=y_col, orientation='h', text=x_col)
    fig.update_traces(marker_color='#719A7E', width=0.15, textposition='outside', textfont=dict(color='#2C3E50', size=12))
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        height=300, margin=dict(l=0, r=20, t=10, b=0),
        xaxis=dict(showgrid=False, showticklabels=False, title=None, range=[0, df[x_col].max()*1.2]),
        yaxis=dict(showgrid=False, title=None, categoryorder='total ascending', tickfont=dict(color='#5D6D7E', size=11))
    )
    return fig

with col_bot1:
    st.markdown('<div class="section-header">SYMPTOM EXPLORER</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">주요 결함-증상 키워드</div>', unsafe_allow_html=True)
    symptom_data = pd.DataFrame({
        'Symptom': ['트레드-벨트 분리 Separation', '진동-밸런스 Vibration', '파열 Blowout', '변형-부풀음 Bulge', '균열-드라이 로트 Cracking', '공기압 손실 Air loss'][::-1],
        'Count': [29, 25, 18, 11, 7, 7][::-1]
    })
    st.plotly_chart(draw_horizontal_bar(symptom_data, 'Count', 'Symptom'), use_container_width=True)

with col_bot2:
    st.markdown('<div class="section-header">PEER COMPARISON</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">제조사·브랜드 비교</div>', unsafe_allow_html=True)
    peer_data = pd.DataFrame({
        'Brand': ['CONTINENTAL', 'GOODYEAR', 'UNKNOWN', 'BRIDGESTONE', 'MICHELIN', 'NEXEN'][::-1],
        'Count': [451, 360, 341, 340, 330, 80][::-1]
    })
    st.plotly_chart(draw_horizontal_bar(peer_data, 'Count', 'Brand'), use_container_width=True)

with col_bot3:
    st.markdown('<div class="section-header">VEHICLE EXPLORER</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">차종별 신고 분포</div>', unsafe_allow_html=True)
    vehicle_data = pd.DataFrame({
        'Vehicle': ['RAM 3500', 'JEEP WRANGLER', 'RAM PROMASTER', 'DODGE JOURNEY', 'GMC SUBURBAN', 'HYUNDAI ELANTRA'][::-1],
        'Count': [29, 8, 6, 2, 2, 2][::-1]
    })
    st.plotly_chart(draw_horizontal_bar(vehicle_data, 'Count', 'Vehicle'), use_container_width=True)

st.markdown("---")
st.markdown("<div style='text-align:center; font-size:11px; color:#A6ACAF;'>신고 건수는 판매량·장착 대수로 보정된 불량률이 아닙니다. 브랜드 언급과 증상 태그는 잠재 신호이며, 타이어의 결함이나 사고 원인을 확정하지 않습니다.</div>", unsafe_allow_html=True)
