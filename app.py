from io import StringIO

import pandas as pd
import requests
import streamlit as st


st.set_page_config(
    page_title="2026 NHTSA 타이어 리콜 대시보드",
    page_icon="🚗",
    layout="wide",
)


GOOGLE_SHEET_ID = "1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk"
GOOGLE_SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/"
    "export?format=csv"
)
TARGET_CAMPAIGN_PREFIX = "26T"

EXPECTED_COLUMNS = [
    "Year",
    "Report_Received_Date",
    "Manufacturer",
    "Component",
    "Campaign_Number",
    "Subject",
    "Summary",
]


@st.cache_data(ttl=3600, show_spinner=False)
def load_real_nhtsa_recalls():
    """Download, validate, normalize, and filter the Google Sheet CSV."""
    response = requests.get(GOOGLE_SHEET_CSV_URL, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(
        StringIO(response.text),
        dtype=str,
        keep_default_na=False,
    )

    df.columns = df.columns.astype(str).str.strip()

    missing_columns = [
        column for column in EXPECTED_COLUMNS if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            "Google Sheet에 필요한 컬럼이 없습니다: "
            + ", ".join(missing_columns)
        )

    df = df[EXPECTED_COLUMNS].copy()

    text_columns = [
        "Year",
        "Manufacturer",
        "Component",
        "Campaign_Number",
        "Subject",
        "Summary",
    ]
    for column in text_columns:
        df[column] = df[column].astype(str).str.strip()

    df["Campaign_Number"] = df["Campaign_Number"].str.upper()
    df["Report_Received_Date"] = pd.to_datetime(
        df["Report_Received_Date"],
        errors="coerce",
    )

    # Never display non-26T rows if unrelated data is added accidentally.
    df = df[df["Campaign_Number"].str.startswith(TARGET_CAMPAIGN_PREFIX)]
    df = df.drop_duplicates(subset=["Campaign_Number"], keep="first")
    df = df.sort_values(
        by=["Report_Received_Date", "Campaign_Number"],
        ascending=[False, False],
        na_position="last",
    )

    return df.reset_index(drop=True)


st.title("🚗 2026 NHTSA 타이어 리콜 대시보드")
st.markdown(
    """
이 대시보드는 **NHTSA 공공 리콜 데이터**를 기반으로 2026년 타이어
리콜 데이터를 보여줍니다. 데이터는 GitHub Actions를 통해 Google Sheets에
정기적으로 업데이트됩니다.
"""
)
st.divider()


try:
    with st.spinner("Google Sheets에서 최신 데이터를 불러오는 중입니다..."):
        df = load_real_nhtsa_recalls()
except Exception as exc:
    st.error(f"Google Sheets 데이터 로딩 중 오류가 발생했습니다: {exc}")
    st.info(
        "Google Sheet의 공유 설정과 CSV 내보내기 권한을 확인해 주세요."
    )
    st.stop()


if df.empty:
    st.warning(
        "현재 Google Sheet에 표시할 2026년 타이어 리콜 데이터가 없습니다."
    )
    st.stop()


st.success(f"총 {len(df):,}건의 2026년 타이어 리콜 데이터를 불러왔습니다.")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("총 리콜 건수", f"{len(df):,} 건")

with col2:
    unique_manufacturers = (
        df["Manufacturer"].replace("", pd.NA).dropna().nunique()
    )
    st.metric("관련 제조사 수", f"{unique_manufacturers:,} 곳")

with col3:
    if df["Report_Received_Date"].notna().any():
        latest_date = df["Report_Received_Date"].max()
        st.metric("최근 신고일", latest_date.strftime("%Y-%m-%d"))
    else:
        st.metric("최근 신고일", "-")


st.subheader("📋 상세 리콜 내역")

display_df = df.copy()
display_df["Report_Received_Date"] = (
    display_df["Report_Received_Date"].dt.strftime("%Y-%m-%d").fillna("")
)

st.dataframe(
    display_df,
    width="stretch",
    hide_index=True,
)
