```python
import streamlit as st
import pandas as pd


# ============================================================
# 1. Page Configuration
# ============================================================

st.set_page_config(
    page_title="2026 NHTSA 타이어 리콜 대시보드",
    page_icon="🚗",
    layout="wide",
)


# ============================================================
# 2. Configuration
# ============================================================

GOOGLE_SHEET_ID = (
    "1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk"
)

GOOGLE_SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{GOOGLE_SHEET_ID}/export?format=csv"
)

# update_data.py에서 생성하는 컬럼과 동일하게 유지
EXPECTED_COLUMNS = [
    "Year",
    "Report_Received_Date",
    "Manufacturer",
    "Component",
    "Campaign_Number",
    "Subject",
    "Summary",
]


# ============================================================
# 3. Google Sheets Data Loading
# ============================================================

@st.cache_data(ttl=3600)
def load_real_nhtsa_recalls():
    """
    Google Sheet 데이터를 CSV 형식으로 읽어온다.

    캐시:
        1시간

    반환:
        pandas DataFrame
    """

    try:

        # ----------------------------------------------------
        # Google Sheet → CSV
        # ----------------------------------------------------

        df = pd.read_csv(
            GOOGLE_SHEET_CSV_URL
        )

        # ----------------------------------------------------
        # 데이터가 없는 경우
        # ----------------------------------------------------

        if df.empty:
            return pd.DataFrame()

        # ----------------------------------------------------
        # 컬럼명 공백 제거
        # ----------------------------------------------------

        df.columns = (
            df.columns
            .astype(str)
            .str.strip()
        )

        # ----------------------------------------------------
        # 필수 컬럼 확인
        # ----------------------------------------------------

        missing_columns = [
            column
            for column in EXPECTED_COLUMNS
            if column not in df.columns
        ]

        if missing_columns:

            raise ValueError(
                "Google Sheet에 필요한 컬럼이 없습니다: "
                + ", ".join(missing_columns)
            )

        # ----------------------------------------------------
        # 문자열 컬럼 정리
        # ----------------------------------------------------

        text_columns = [
            "Manufacturer",
            "Component",
            "Campaign_Number",
            "Subject",
            "Summary",
        ]

        for column in text_columns:

            if column in df.columns:

                df[column] = (
                    df[column]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

        # ----------------------------------------------------
        # 날짜 컬럼 처리
        # ----------------------------------------------------

        if "Report_Received_Date" in df.columns:

            df["Report_Received_Date"] = pd.to_datetime(
                df["Report_Received_Date"],
                errors="coerce",
            )

        # ----------------------------------------------------
        # Campaign Number 정리
        # ----------------------------------------------------

        if "Campaign_Number" in df.columns:

            df["Campaign_Number"] = (
                df["Campaign_Number"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

        # ----------------------------------------------------
        # 최신 신고일 순으로 정렬
        # ----------------------------------------------------

        if "Report_Received_Date" in df.columns:

            df = df.sort_values(
                by="Report_Received_Date",
                ascending=False,
                na_position="last",
            )

        # ----------------------------------------------------
        # Index 초기화
        # ----------------------------------------------------

        df = df.reset_index(drop=True)

        return df

    except Exception as e:

        st.error(
            f"구글 시트 연동 중 오류가 발생했습니다: {e}"
        )

        return pd.DataFrame()


# ============================================================
# 4. Page Header
# ============================================================

st.title(
    "🚗 2026 NHTSA 타이어 리콜 대시보드"
)

st.markdown(
    """
이 대시보드는 **NHTSA 공공 리콜 데이터**를 기반으로
2026년 타이어 리콜 데이터를 보여줍니다.

NHTSA 데이터는 GitHub Actions를 통해 자동으로 수집되어
Google Sheets에 업데이트되며,
본 대시보드는 Google Sheets의 데이터를 읽어 표시합니다.
"""
)

st.divider()


# ============================================================
# 5. Load Data
# ============================================================

with st.spinner(
    "구글 시트에서 최신 데이터를 불러오는 중입니다..."
):

    df = load_real_nhtsa_recalls()


# ============================================================
# 6. Empty Data
# ============================================================

if df.empty:

    st.info(
        "💡 현재 Google Sheet에 표시할 "
        "2026년 타이어 리콜 데이터가 없습니다."
    )

    st.stop()


# ============================================================
# 7. Success Message
# ============================================================

st.success(
    f"✅ 총 {len(df):,}건의 "
    "2026년 타이어 리콜 데이터를 성공적으로 불러왔습니다."
)


# ============================================================
# 8. Summary Metrics
# ============================================================

col1, col2, col3 = st.columns(3)


# ------------------------------------------------------------
# Total Recall Count
# ------------------------------------------------------------

with col1:

    st.metric(
        label="총 리콜 건수",
        value=f"{len(df):,} 건",
    )


# ------------------------------------------------------------
# Manufacturer Count
# ------------------------------------------------------------

with col2:

    if "Manufacturer" in df.columns:

        unique_mfg = (
            df["Manufacturer"]
            .replace("", pd.NA)
            .dropna()
            .nunique()
        )

        st.metric(
            label="관련 제조사 수",
            value=f"{unique_mfg:,} 곳",
        )

    else:

        st.metric(
            label="관련 제조사 수",
            value="-",
        )


# ------------------------------------------------------------
# Latest Report Date
# ------------------------------------------------------------

with col3:

    if (
        "Report_Received_Date" in df.columns
        and df["Report_Received_Date"].notna().any()
    ):

        latest_date = (
            df["Report_Received_Date"]
            .max()
        )

        st.metric(
            label="최근 신고일",
            value=latest_date.strftime(
                "%Y-%m-%d"
            ),
        )

    else:

        st.metric(
            label="최근 신고일",
            value="-",
        )


# ============================================================
# 9. Detailed Recall Data
# ============================================================

st.write(
    "### 📋 상세 리콜 내역"
)


# ------------------------------------------------------------
# Display용 DataFrame 생성
# ------------------------------------------------------------

display_df = df.copy()


# ------------------------------------------------------------
# 날짜를 화면에서는 YYYY-MM-DD로 표시
# ------------------------------------------------------------

if "Report_Received_Date" in display_df.columns:

    display_df["Report_Received_Date"] = (
        display_df["Report_Received_Date"]
        .dt.strftime("%Y-%m-%d")
        .fillna("")
    )


# ============================================================
# 10. Data Table
# ============================================================

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)
```

이 버전에서는 `update_data.py`의 다음 컬럼을 그대로 사용합니다.

```text
Year
Report_Received_Date
Manufacturer
Component
Campaign_Number
Subject
Summary
```

따라서 **`app.py`와 `update_data.py` 사이의 컬럼명 불일치는 없습니다.**

또한 NHTSA API 자체는 `app.py`에서 호출하지 않습니다. `app.py`는 Google Sheet만 읽기 때문에, NHTSA API가 일시적으로 400/500을 반환하더라도 대시보드 자체가 영향을 받지 않습니다. API 오류 처리는 `update_data.py`에서 담당하고, Streamlit은 **마지막으로 정상 저장된 Google Sheet 데이터를 계속 보여주는 구조**입니다.

한 가지 주의할 점은 현재 `@st.cache_data(ttl=3600)` 때문에 **Google Sheet가 변경된 직후에도 최대 약 1시간 동안 이전 데이터가 보일 수 있다는 것**입니다. 매주 업데이트되는 대시보드라면 현재 설정은 충분히 합리적입니다.
