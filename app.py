import streamlit as st
import pandas as pd

# 1. 페이지 기본 설정 (가장 먼저 와야 함)
st.set_page_config(
    page_title="2026 NHTSA 타이어 리콜 대시보드",
    page_icon="🚗",
    layout="wide"
)

# 2. 구글 시트 데이터 로딩 함수 (캐싱 적용으로 속도 최적화)
@st.cache_data(ttl=3600)
def load_real_nhtsa_recalls():
    try:
        # 구글 시트 데이터를 CSV 형태로 직접 고속 다운로드
        sheet_id = "1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk"
        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        
        df = pd.read_csv(csv_url)
        
        # 데이터가 있고, 날짜 컬럼이 존재할 경우에만 포맷 변환
        if not df.empty and 'Report_Received_Date' in df.columns:
            df['Report_Received_Date'] = pd.to_datetime(df['Report_Received_Date'], errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"구글 시트 연동 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# 3. 대시보드 UI 구성
st.title("🚗 2026 NHTSA 타이어 리콜 대시보드")
st.markdown("""
이 대시보드는 깃허브 자동화(GitHub Actions)를 통해 **매주 금요일 정오에 자동으로 업데이트**되는 구글 시트 데이터를 기반으로 작동합니다.
API 지연 없이 언제나 빠르고 쾌적하게 데이터를 확인할 수 있습니다.
""")
st.divider()

# 데이터 불러오기
with st.spinner("구글 시트에서 최신 데이터를 불러오는 중입니다..."):
    df = load_real_nhtsa_recalls()

# 4. 결과 화면 출력
if df.empty:
    st.info("💡 현재 구글 시트에 기록된 2026년 타이어 리콜 데이터가 없습니다. (데이터가 추가되면 자동으로 이곳에 표시됩니다.)")
else:
    st.success(f"✅ 총 {len(df)}건의 2026년 타이어 리콜 데이터를 성공적으로 불러왔습니다.")
    
    # 요약 지표 (Metrics)
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="총 리콜 건수", value=f"{len(df)} 건")
    with col2:
        if 'Manufacturer' in df.columns:
            unique_mfg = df['Manufacturer'].nunique()
            st.metric(label="관련 제조사 수", value=f"{unique_mfg} 곳")
        else:
            st.metric(label="관련 제조사 수", value="-")

    st.write("### 📋 상세 리콜 내역")
    # 표 형태로 깔끔하게 데이터 출력
    st.dataframe(df, use_container_width=True, hide_index=True)
