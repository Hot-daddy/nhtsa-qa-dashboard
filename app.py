from io import StringIO

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


st.set_page_config(
    page_title="NHTSA 타이어 품질 모니터링",
    page_icon="🚗",
    layout="wide",
)


GOOGLE_SHEET_ID = "1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk"
RECALL_SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/"
    "export?format=csv"
)
COMPLAINT_SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/"
    "gviz/tq?tqx=out:csv&sheet=Tire_Complaints"
)

TARGET_CAMPAIGN_PREFIX = "26T"
REQUEST_TIMEOUT = 30

RECALL_COLUMNS = [
    "Year",
    "Report_Received_Date",
    "Manufacturer",
    "Component",
    "Campaign_Number",
    "Subject",
    "Summary",
]

COMPLAINT_COLUMNS = [
    "ODI_Number",
    "Complaint_Received_Date",
    "Failure_Date",
    "Brand_Original",
    "Brand_Standard",
    "Brand_Confidence",
    "Pattern_Original",
    "Pattern_Standard",
    "Pattern_Source",
    "Pattern_Confidence",
    "Pattern_Review_Required",
    "Manufacturer",
    "Component",
    "DOT",
    "DOT_Plant_Code",
    "DOT_Production_Week",
    "DOT_Production_Year",
    "Tire_Size",
    "Product_Year",
    "Vehicle_Context",
    "Mileage",
    "Vehicle_Speed",
    "OE_RE",
    "Tire_Location",
    "NHTSA_Failure_Code",
    "Primary_Issue",
    "Secondary_Issues",
    "Safety_Risk",
    "Warranty_Complaint_YN",
    "Crash_YN",
    "Fire_YN",
    "Injuries",
    "Deaths",
    "Medical_Attention_YN",
    "Towed_YN",
    "Incident_State",
    "Description",
    "Source_URL",
    "Data_Quality_Flags",
]

RISK_ORDER = ["Critical", "High", "Medium", "Low"]
RISK_COLORS = {
    "Critical": "#B91C1C",
    "High": "#EA580C",
    "Medium": "#D97706",
    "Low": "#2563EB",
}


def fetch_csv(url):
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": "NHTSA-Tire-Quality-Dashboard/2.0"},
    )
    response.raise_for_status()
    return pd.read_csv(
        StringIO(response.content.decode("utf-8-sig")),
        dtype=str,
        keep_default_na=False,
    )


def validate_columns(df, expected_columns, source_name):
    df.columns = df.columns.astype(str).str.strip()
    missing_columns = [
        column for column in expected_columns if column not in df.columns
    ]
    if missing_columns:
        raise ValueError(
            f"{source_name}에 필요한 컬럼이 없습니다: "
            + ", ".join(missing_columns)
        )
    return df[expected_columns].copy()


@st.cache_data(ttl=3600, show_spinner=False)
def load_recalls():
    df = fetch_csv(RECALL_SHEET_CSV_URL)
    df = validate_columns(df, RECALL_COLUMNS, "리콜 시트")

    for column in RECALL_COLUMNS:
        df[column] = df[column].astype(str).str.strip()

    df["Campaign_Number"] = df["Campaign_Number"].str.upper()
    df["Report_Received_Date"] = pd.to_datetime(
        df["Report_Received_Date"],
        errors="coerce",
    )
    df = df[df["Campaign_Number"].str.startswith(TARGET_CAMPAIGN_PREFIX)]
    df = df.drop_duplicates(subset=["Campaign_Number"], keep="first")
    df = df.sort_values(
        ["Report_Received_Date", "Campaign_Number"],
        ascending=[False, False],
        na_position="last",
    )
    return df.reset_index(drop=True)


@st.cache_data(ttl=3600, show_spinner=False)
def load_complaints():
    df = fetch_csv(COMPLAINT_SHEET_CSV_URL)
    df = validate_columns(df, COMPLAINT_COLUMNS, "불만 시트")

    for column in COMPLAINT_COLUMNS:
        df[column] = df[column].astype(str).str.strip()

    for column in ["Complaint_Received_Date", "Failure_Date"]:
        df[column] = pd.to_datetime(df[column], errors="coerce")

    for column in ["Mileage", "Vehicle_Speed", "Injuries", "Deaths"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["ODI_Number"] = df["ODI_Number"].str.strip()
    df = df[df["ODI_Number"] != ""]
    df = df.drop_duplicates(subset=["ODI_Number"], keep="first")
    df = df.sort_values(
        ["Complaint_Received_Date", "ODI_Number"],
        ascending=[False, False],
        na_position="last",
    )
    return df.reset_index(drop=True)


def load_data_safely(loader):
    try:
        return loader(), ""
    except Exception as exc:
        return pd.DataFrame(), str(exc)


def split_issue_values(df):
    values = set(df["Primary_Issue"].replace("", pd.NA).dropna())
    for secondary_value in df["Secondary_Issues"]:
        values.update(
            value.strip()
            for value in secondary_value.split("|")
            if value.strip()
        )
    return sorted(values)


def create_issue_counts(df):
    issues = []
    for _, row in df.iterrows():
        row_issues = [row["Primary_Issue"]]
        row_issues.extend(row["Secondary_Issues"].split("|"))
        issues.extend(
            issue.strip()
            for issue in row_issues
            if issue and issue.strip()
        )

    if not issues:
        return pd.DataFrame(columns=["Issue", "Complaint_Count"])

    return (
        pd.Series(issues, name="Issue")
        .value_counts()
        .rename_axis("Issue")
        .reset_index(name="Complaint_Count")
    )


def apply_non_brand_filters(
    df,
    start_date,
    end_date,
    selected_issues,
    selected_risks,
    selected_oe_re,
    review_only,
):
    filtered = df.copy()

    if start_date and end_date:
        dates = filtered["Complaint_Received_Date"].dt.date
        filtered = filtered[(dates >= start_date) & (dates <= end_date)]

    if selected_issues:
        combined_issues = (
            filtered["Primary_Issue"]
            + " | "
            + filtered["Secondary_Issues"]
        )
        issue_mask = pd.Series(False, index=filtered.index)
        for selected_issue in selected_issues:
            issue_mask = issue_mask | combined_issues.str.contains(
                selected_issue,
                case=False,
                regex=False,
                na=False,
            )
        filtered = filtered[issue_mask]

    if selected_risks:
        filtered = filtered[filtered["Safety_Risk"].isin(selected_risks)]

    if selected_oe_re:
        filtered = filtered[filtered["OE_RE"].isin(selected_oe_re)]

    if review_only:
        review_mask = (
            filtered["Pattern_Review_Required"].eq("Y")
            | filtered["Data_Quality_Flags"].ne("")
        )
        filtered = filtered[review_mask]

    return filtered


def format_date_column(df, column):
    if column in df.columns:
        df[column] = df[column].dt.strftime("%Y-%m-%d").fillna("")
    return df


def show_empty(message):
    st.info(message)


st.title("🚗 NHTSA 타이어 품질 모니터링")
st.caption(
    "NHTSA 공식 리콜 및 소비자 불만 데이터를 이용한 브랜드·불만 유형·"
    "NEXEN 패턴별 품질 신호 모니터링"
)

with st.spinner("Google Sheets에서 최신 데이터를 불러오는 중입니다..."):
    recalls_df, recall_error = load_data_safely(load_recalls)
    complaints_df, complaint_error = load_data_safely(load_complaints)

if recall_error:
    st.warning(f"리콜 데이터 로딩 오류: {recall_error}")
if complaint_error:
    st.warning(
        "불만 데이터 탭을 아직 불러올 수 없습니다. GitHub Actions에서 "
        f"update_complaints.py를 먼저 실행해 주세요. 상세 오류: {complaint_error}"
    )


if not complaints_df.empty:
    valid_dates = complaints_df["Complaint_Received_Date"].dropna()
    min_date = valid_dates.min().date() if not valid_dates.empty else None
    max_date = valid_dates.max().date() if not valid_dates.empty else None

    st.sidebar.header("불만 데이터 필터")
    selected_date_range = st.sidebar.date_input(
        "NHTSA 접수일",
        value=(min_date, max_date) if min_date and max_date else (),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(selected_date_range, (tuple, list)) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
    else:
        start_date = min_date
        end_date = max_date

    brand_options = sorted(
        complaints_df["Brand_Standard"].replace("", pd.NA).dropna().unique()
    )
    selected_brands = st.sidebar.multiselect(
        "브랜드",
        brand_options,
        default=[],
        help="선택하지 않으면 모든 브랜드를 포함합니다.",
    )

    issue_options = split_issue_values(complaints_df)
    selected_issues = st.sidebar.multiselect(
        "불만 유형",
        issue_options,
        default=[],
    )

    available_risks = [
        risk for risk in RISK_ORDER if risk in set(complaints_df["Safety_Risk"])
    ]
    selected_risks = st.sidebar.multiselect(
        "Safety Risk",
        available_risks,
        default=[],
    )

    oe_re_options = sorted(
        complaints_df["OE_RE"].replace("", pd.NA).dropna().unique()
    )
    selected_oe_re = st.sidebar.multiselect(
        "OE/RE",
        oe_re_options,
        default=[],
    )
    review_only = st.sidebar.checkbox("수동 검토 필요 건만 표시", value=False)

    base_filtered_df = apply_non_brand_filters(
        complaints_df,
        start_date,
        end_date,
        selected_issues,
        selected_risks,
        selected_oe_re,
        review_only,
    )
    filtered_complaints_df = base_filtered_df.copy()
    if selected_brands:
        filtered_complaints_df = filtered_complaints_df[
            filtered_complaints_df["Brand_Standard"].isin(selected_brands)
        ]
else:
    base_filtered_df = pd.DataFrame()
    filtered_complaints_df = pd.DataFrame()


tabs = st.tabs(
    [
        "Overview",
        "Brand Comparison",
        "NEXEN Pattern",
        "2026 Recalls",
        "Complaint Details",
    ]
)


with tabs[0]:
    if filtered_complaints_df.empty:
        show_empty("현재 조건에 표시할 타이어 불만 데이터가 없습니다.")
    else:
        total_complaints = len(filtered_complaints_df)
        brand_count = filtered_complaints_df["Brand_Standard"].nunique()
        nexen_count = int(
            filtered_complaints_df["Brand_Standard"].eq("NEXEN").sum()
        )
        high_risk_count = int(
            filtered_complaints_df["Safety_Risk"].isin(["Critical", "High"]).sum()
        )
        latest_date = filtered_complaints_df["Complaint_Received_Date"].max()

        metric_columns = st.columns(5)
        metric_columns[0].metric("고유 불만 건수", f"{total_complaints:,} 건")
        metric_columns[1].metric("관련 브랜드", f"{brand_count:,} 개")
        metric_columns[2].metric("NEXEN 불만", f"{nexen_count:,} 건")
        metric_columns[3].metric("High/Critical", f"{high_risk_count:,} 건")
        metric_columns[4].metric(
            "최근 접수일",
            latest_date.strftime("%Y-%m-%d") if pd.notna(latest_date) else "-",
        )

        left_chart, right_chart = st.columns(2)

        with left_chart:
            monthly = (
                filtered_complaints_df.dropna(subset=["Complaint_Received_Date"])
                .assign(
                    Month=lambda frame: frame["Complaint_Received_Date"]
                    .dt.to_period("M")
                    .dt.to_timestamp()
                )
                .groupby("Month", as_index=False)
                .size()
                .rename(columns={"size": "Complaint_Count"})
            )
            trend_figure = px.line(
                monthly,
                x="Month",
                y="Complaint_Count",
                markers=True,
                title="월별 고유 불만 추이",
                labels={"Month": "접수 월", "Complaint_Count": "불만 건수"},
            )
            trend_figure.update_layout(height=410, margin=dict(l=20, r=20, t=55, b=20))
            st.plotly_chart(trend_figure, width="stretch", config={"displayModeBar": False})

        with right_chart:
            brand_counts = (
                filtered_complaints_df["Brand_Standard"]
                .replace("", "UNKNOWN")
                .value_counts()
                .head(15)
                .sort_values()
                .rename_axis("Brand")
                .reset_index(name="Complaint_Count")
            )
            brand_figure = px.bar(
                brand_counts,
                x="Complaint_Count",
                y="Brand",
                orientation="h",
                title="브랜드별 고유 불만 건수",
                labels={"Complaint_Count": "불만 건수", "Brand": "브랜드"},
            )
            brand_figure.update_layout(height=410, margin=dict(l=20, r=20, t=55, b=20))
            st.plotly_chart(brand_figure, width="stretch", config={"displayModeBar": False})

        issue_counts = create_issue_counts(filtered_complaints_df).head(15)
        if not issue_counts.empty:
            issue_figure = px.bar(
                issue_counts.sort_values("Complaint_Count"),
                x="Complaint_Count",
                y="Issue",
                orientation="h",
                title="주요 불만 유형 — 하나의 불만에 여러 유형이 포함될 수 있음",
                labels={"Complaint_Count": "포함된 불만 건수", "Issue": "불만 유형"},
            )
            issue_figure.update_layout(height=500, margin=dict(l=20, r=20, t=55, b=20))
            st.plotly_chart(issue_figure, width="stretch", config={"displayModeBar": False})

        st.caption(
            "불만 건수는 ODINO 기준 고유 사례 수입니다. 브랜드별 판매량이 반영되지 "
            "않은 원시 건수이므로 시장 품질률로 직접 해석해서는 안 됩니다."
        )


with tabs[1]:
    if filtered_complaints_df.empty:
        show_empty("현재 조건에 비교할 브랜드 데이터가 없습니다.")
    else:
        comparison = (
            filtered_complaints_df.assign(
                High_Risk=filtered_complaints_df["Safety_Risk"].isin(
                    ["Critical", "High"]
                ),
                Crash=filtered_complaints_df["Crash_YN"].eq("Y"),
                Review=filtered_complaints_df["Data_Quality_Flags"].ne(""),
            )
            .groupby("Brand_Standard", as_index=False)
            .agg(
                Complaint_Count=("ODI_Number", "nunique"),
                High_Risk_Count=("High_Risk", "sum"),
                Crash_Count=("Crash", "sum"),
                Injuries=("Injuries", "sum"),
                Review_Count=("Review", "sum"),
            )
        )
        comparison["High_Risk_Rate"] = (
            comparison["High_Risk_Count"] / comparison["Complaint_Count"]
        )
        comparison = comparison.sort_values("Complaint_Count", ascending=False)

        top_comparison = comparison.head(20).sort_values("Complaint_Count")
        comparison_figure = px.bar(
            top_comparison,
            x="Complaint_Count",
            y="Brand_Standard",
            orientation="h",
            color="High_Risk_Count",
            color_continuous_scale="OrRd",
            title="브랜드별 불만 및 High/Critical 신호",
            labels={
                "Complaint_Count": "고유 불만 건수",
                "Brand_Standard": "브랜드",
                "High_Risk_Count": "High/Critical",
            },
        )
        comparison_figure.update_layout(height=600, margin=dict(l=20, r=20, t=55, b=20))
        st.plotly_chart(
            comparison_figure,
            width="stretch",
            config={"displayModeBar": False},
        )

        comparison_display = comparison.copy()
        comparison_display["High_Risk_Rate"] = comparison_display[
            "High_Risk_Rate"
        ].map(lambda value: f"{value:.1%}")
        st.dataframe(
            comparison_display,
            width="stretch",
            hide_index=True,
        )
        st.caption(
            "브랜드별 비교는 NHTSA 신고 건수 비교이며 판매량 또는 시장점유율로 "
            "보정되지 않았습니다."
        )


with tabs[2]:
    if base_filtered_df.empty:
        show_empty("현재 조건에 NEXEN 분석 데이터가 없습니다.")
    else:
        nexen_df = base_filtered_df[
            base_filtered_df["Brand_Standard"].eq("NEXEN")
        ].copy()

        if nexen_df.empty:
            show_empty("현재 조건에 NEXEN 불만 데이터가 없습니다.")
        else:
            pattern_options = sorted(
                nexen_df["Pattern_Standard"].replace("", "UNKNOWN").unique()
            )
            selected_patterns = st.multiselect(
                "NEXEN 패턴",
                pattern_options,
                default=[],
                key="nexen_pattern_filter",
                help="선택하지 않으면 모든 NEXEN 패턴을 포함합니다.",
            )
            if selected_patterns:
                nexen_df = nexen_df[
                    nexen_df["Pattern_Standard"].isin(selected_patterns)
                ]

            review_count = int(
                (
                    nexen_df["Pattern_Review_Required"].eq("Y")
                    | nexen_df["Data_Quality_Flags"].ne("")
                ).sum()
            )
            high_risk_count = int(
                nexen_df["Safety_Risk"].isin(["Critical", "High"]).sum()
            )
            known_patterns = nexen_df.loc[
                nexen_df["Pattern_Standard"].ne("UNKNOWN"),
                "Pattern_Standard",
            ].nunique()

            metric_columns = st.columns(4)
            metric_columns[0].metric("NEXEN 고유 불만", f"{len(nexen_df):,} 건")
            metric_columns[1].metric("식별된 패턴", f"{known_patterns:,} 개")
            metric_columns[2].metric("High/Critical", f"{high_risk_count:,} 건")
            metric_columns[3].metric("검토 필요", f"{review_count:,} 건")

            chart_left, chart_right = st.columns(2)
            with chart_left:
                pattern_counts = (
                    nexen_df["Pattern_Standard"]
                    .replace("", "UNKNOWN")
                    .value_counts()
                    .sort_values()
                    .rename_axis("Pattern")
                    .reset_index(name="Complaint_Count")
                )
                pattern_figure = px.bar(
                    pattern_counts,
                    x="Complaint_Count",
                    y="Pattern",
                    orientation="h",
                    title="NEXEN 패턴별 고유 불만",
                    labels={"Complaint_Count": "불만 건수", "Pattern": "패턴"},
                )
                pattern_figure.update_layout(
                    height=max(420, 28 * len(pattern_counts)),
                    margin=dict(l=20, r=20, t=55, b=20),
                )
                st.plotly_chart(
                    pattern_figure,
                    width="stretch",
                    config={"displayModeBar": False},
                )

            with chart_right:
                nexen_issue_counts = create_issue_counts(nexen_df).head(15)
                issue_figure = px.bar(
                    nexen_issue_counts.sort_values("Complaint_Count"),
                    x="Complaint_Count",
                    y="Issue",
                    orientation="h",
                    title="NEXEN 주요 불만 유형",
                    labels={"Complaint_Count": "포함된 불만 건수", "Issue": "유형"},
                )
                issue_figure.update_layout(
                    height=max(420, 28 * len(nexen_issue_counts)),
                    margin=dict(l=20, r=20, t=55, b=20),
                )
                st.plotly_chart(
                    issue_figure,
                    width="stretch",
                    config={"displayModeBar": False},
                )

            nexen_display_columns = [
                "ODI_Number",
                "Complaint_Received_Date",
                "Pattern_Standard",
                "Pattern_Original",
                "Pattern_Confidence",
                "Tire_Size",
                "DOT",
                "DOT_Plant_Code",
                "DOT_Production_Week",
                "DOT_Production_Year",
                "OE_RE",
                "Primary_Issue",
                "Safety_Risk",
                "Vehicle_Context",
                "Mileage",
                "Data_Quality_Flags",
                "Description",
                "Source_URL",
            ]
            nexen_display = nexen_df[nexen_display_columns].copy()
            nexen_display = format_date_column(
                nexen_display,
                "Complaint_Received_Date",
            )
            st.dataframe(
                nexen_display,
                width="stretch",
                hide_index=True,
                column_config={
                    "Source_URL": st.column_config.LinkColumn(
                        "NHTSA Source",
                        display_text="Open",
                    )
                },
            )


with tabs[3]:
    if recalls_df.empty:
        show_empty("현재 Google Sheet에 표시할 2026년 타이어 리콜이 없습니다.")
    else:
        recall_metrics = st.columns(3)
        recall_metrics[0].metric("총 리콜", f"{len(recalls_df):,} 건")
        recall_metrics[1].metric(
            "관련 제조사",
            f"{recalls_df['Manufacturer'].replace('', pd.NA).dropna().nunique():,} 곳",
        )
        latest_recall_date = recalls_df["Report_Received_Date"].max()
        recall_metrics[2].metric(
            "최근 신고일",
            latest_recall_date.strftime("%Y-%m-%d")
            if pd.notna(latest_recall_date)
            else "-",
        )

        recall_display = recalls_df.copy()
        recall_display = format_date_column(recall_display, "Report_Received_Date")
        st.dataframe(recall_display, width="stretch", hide_index=True)


with tabs[4]:
    if filtered_complaints_df.empty:
        show_empty("현재 조건에 표시할 원문 불만 데이터가 없습니다.")
    else:
        search_text = st.text_input(
            "ODI 번호, 브랜드, 패턴 또는 원문 검색",
            value="",
            key="complaint_text_search",
        ).strip()
        detail_df = filtered_complaints_df.copy()
        if search_text:
            searchable_columns = [
                "ODI_Number",
                "Brand_Standard",
                "Pattern_Standard",
                "Tire_Size",
                "DOT",
                "Description",
            ]
            search_mask = pd.Series(False, index=detail_df.index)
            for column in searchable_columns:
                search_mask = search_mask | detail_df[column].str.contains(
                    search_text,
                    case=False,
                    regex=False,
                    na=False,
                )
            detail_df = detail_df[search_mask]

        st.write(f"표시 결과: **{len(detail_df):,}건**")
        detail_columns = [
            "ODI_Number",
            "Complaint_Received_Date",
            "Brand_Standard",
            "Pattern_Standard",
            "Tire_Size",
            "DOT",
            "OE_RE",
            "Primary_Issue",
            "Secondary_Issues",
            "Safety_Risk",
            "Crash_YN",
            "Injuries",
            "Deaths",
            "Vehicle_Context",
            "Mileage",
            "Incident_State",
            "Data_Quality_Flags",
            "Description",
            "Source_URL",
        ]
        detail_display = detail_df[detail_columns].copy()
        detail_display = format_date_column(
            detail_display,
            "Complaint_Received_Date",
        )
        st.dataframe(
            detail_display,
            width="stretch",
            hide_index=True,
            column_config={
                "Source_URL": st.column_config.LinkColumn(
                    "NHTSA Source",
                    display_text="Open",
                )
            },
        )
        st.download_button(
            "필터 결과 CSV 다운로드",
            data=detail_display.to_csv(index=False).encode("utf-8-sig"),
            file_name="nhtsa_tire_complaints_filtered.csv",
            mime="text/csv",
        )


with st.expander("데이터 정의 및 해석 기준"):
    st.markdown(
        """
- 불만 건수는 원본 행 수가 아니라 **ODINO 기준 고유 사례 수**입니다.
- 하나의 불만은 여러 불만 유형을 동시에 가질 수 있으므로 유형별 건수의 합은
  전체 불만 건수보다 클 수 있습니다.
- NEXEN 패턴은 불만 원문의 패턴명, `MODELTXT`, 패턴 표준화 사전을 순서대로
  사용해 분류하며 충돌 또는 미확인 건은 검토 대상으로 표시합니다.
- NHTSA 불만은 안전 관련 자발적 신고이며 전체 Warranty Claim을 의미하지 않습니다.
- 브랜드별 건수는 판매량으로 보정되지 않은 원시 건수입니다.
"""
    )
