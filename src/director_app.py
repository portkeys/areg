"""
Event Director Portal - Streamlit App

Participant analytics for event directors scoped to their own data.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

from data_loader import (
    get_promoter_ids,
    get_promoter_data,
    get_promoter_events,
    get_promoter_summary,
    get_promoter_event_center,
)
from analytics import EventAnalytics
from llm_client import (
    generate_dashboard_insight,
    generate_sponsor_pitch,
)


# Page config
st.set_page_config(
    page_title="Event Director Portal",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Outside Brand Colors
OUTSIDE_COLORS = {
    "primary": "#FFD100",
    "primary_dark": "#E6BC00",
    "primary_light": "#FFF3B0",
    "secondary": "#000000",
    "secondary_light": "#1a1a1a",
    "accent": "#333333",
    "text": "#000000",
    "text_light": "#555555",
    "text_muted": "#666666",
    "bg": "#F7F7F7",
    "card_bg": "#FFFFFF",
    "warm_bg": "#fffbea",
}

CHART_COLORS = [
    "#FFD100", "#000000", "#333333", "#666666",
    "#999999", "#E6BC00", "#B8960A", "#CCCCCC",
]

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #F7F7F7; }
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }
    .insight-box {
        background-color: #fffbea;
        border-left: 4px solid #FFD100;
        padding: 15px;
        margin: 15px 0;
        border-radius: 0 12px 12px 0;
    }
    [data-testid="stSidebar"] { background-color: #000000; }
    [data-testid="stSidebar"] .stMarkdown { color: #FFFFFF; }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #FFD100 !important; }
    [data-testid="stSidebar"] label { color: #FFFFFF !important; }
    [data-testid="stSidebar"] .stSelectbox label { color: #FFFFFF !important; }
    [data-testid="stSidebar"] .stRadio label { color: #FFFFFF !important; }
    [data-testid="stSidebar"] .stRadio p { color: #FFFFFF !important; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #FFFFFF !important; }
    .stButton > button[kind="primary"] {
        background-color: #FFD100; color: #000000; border: none; font-weight: 600;
    }
    .stButton > button[kind="primary"]:hover { background-color: #E6BC00; color: #000000; }
    .stButton > button { border: 1px solid #E0E0E0; border-radius: 8px; }
    .stButton > button:hover { border-color: #FFD100; background-color: #fffbea; }
    [data-testid="stMetricValue"] { color: #000000; }
    [data-testid="stMetricDelta"] svg { stroke: #FFD100; }
    h1, h2, h3 { color: #000000; }
    [data-testid="stExpander"] { border: 1px solid #E0E0E0; border-radius: 12px; }
    .sponsor-pitch {
        background-color: #FFFFFF;
        border: 2px solid #FFD100;
        border-radius: 16px;
        padding: 30px;
        margin: 20px 0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    if "promoter_id" not in st.session_state:
        st.session_state.promoter_id = None
    if "df" not in st.session_state:
        st.session_state.df = None
    if "analytics" not in st.session_state:
        st.session_state.analytics = None
    if "event_center" not in st.session_state:
        st.session_state.event_center = None


def render_sidebar():
    with st.sidebar:
        st.title("Event Director Portal")
        st.markdown("---")

        st.subheader("Your Event Series")
        promoters = get_promoter_ids()
        options = {f"{name} ({count} events)": pid for pid, name, count in promoters}
        selected = st.selectbox(
            "Select Event Series",
            options=list(options.keys()),
            index=0 if options else None,
        )

        if selected:
            promoter_id = options[selected]
            if promoter_id != st.session_state.promoter_id:
                st.session_state.promoter_id = promoter_id
                st.session_state.df = get_promoter_data(promoter_id)
                st.session_state.analytics = EventAnalytics(st.session_state.df)
                st.session_state.segment_result = None
                try:
                    st.session_state.event_center = get_promoter_event_center(promoter_id)
                except Exception:
                    st.session_state.event_center = (0.0, 0.0, "Unknown", "Unknown")

        st.markdown("---")

        st.subheader("Navigation")
        page = st.radio(
            "Go to",
            options=[
                "Audience Profile",
                "Retention",
                "Segment Builder",
                "YoY Trends",
                "Sponsor Pitch",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")

        # Show event summary
        if st.session_state.promoter_id:
            summary = get_promoter_summary(st.session_state.promoter_id)
            st.caption(f"Events: {summary['total_events']}")
            st.caption(f"Participants: {summary['unique_participants']:,}")
            if summary["years_active"]:
                st.caption(f"Years: {min(summary['years_active'])}-{max(summary['years_active'])}")

        return page


# ---------------------------------------------------------------------------
# Page 1: Audience Profile (Demographics)
# ---------------------------------------------------------------------------
def render_demographics():
    st.title("Audience Profile")

    if st.session_state.df is None or st.session_state.df.empty:
        st.warning("No data available. Please select an event series.")
        return

    df = st.session_state.df
    analytics = st.session_state.analytics
    event_lat, event_lon, event_city, event_state = st.session_state.event_center

    years = sorted(df["event_year"].dropna().unique().astype(int), reverse=True)
    year = st.selectbox("Year", years, index=0)

    year_df = df[df["event_year"] == year]
    total_participants = year_df["participant_id"].nunique()

    # Age stats
    ages = year_df.groupby("participant_id")["participant_age"].first().dropna()
    median_age = float(ages.median()) if len(ages) > 0 else 0

    # Gender
    gender = analytics.get_gender_distribution(year)
    total_g = sum(gender.values()) if gender else 0
    m_pct = round(gender.get("M", 0) / total_g * 100) if total_g > 0 else 0
    f_pct = round(gender.get("F", 0) / total_g * 100) if total_g > 0 else 0

    # Distance
    dist_data = analytics.get_distance_distribution(event_lat, event_lon) if event_lat else {}
    avg_distance = dist_data.get("avg_miles", 0)

    # Metric cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Participants", f"{total_participants:,}")
    c2.metric("Median Age", f"{median_age:.0f}")
    c3.metric("Gender Split", f"{m_pct}% M / {f_pct}% F")
    c4.metric("Avg Distance", f"{avg_distance:.0f} mi")

    # Charts row 1: Age + Gender
    col1, col2 = st.columns(2)

    with col1:
        age_dist = analytics.get_age_distribution(year)
        if not age_dist.empty:
            fig = px.bar(
                age_dist, x="count", y="age_group", orientation="h",
                title="Age Distribution",
                color_discrete_sequence=[OUTSIDE_COLORS["primary"]],
            )
            fig.update_layout(paper_bgcolor="white", yaxis_title="", xaxis_title="Participants")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if gender and total_g > 0:
            gender_df = pd.DataFrame([
                {"Gender": k, "Count": v} for k, v in gender.items() if v > 0
            ])
            fig = px.pie(
                gender_df, values="Count", names="Gender",
                title="Gender Distribution",
                color_discrete_sequence=CHART_COLORS,
            )
            fig.update_layout(paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)

    # Charts row 2: Experience + Distance
    col1, col2 = st.columns(2)

    with col1:
        exp_dist = analytics.get_experience_distribution(year)
        if not exp_dist.empty:
            fig = px.pie(
                exp_dist, values="count", names="experience_level",
                title="Experience Level",
                color_discrete_sequence=["#999999", "#666666", "#333333", "#FFD100"],
            )
            fig.update_layout(paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if dist_data and "buckets" in dist_data:
            bucket_df = pd.DataFrame([
                {"Distance": "Under 25 mi", "Count": dist_data["buckets"]["under_25"]},
                {"Distance": "25-50 mi", "Count": dist_data["buckets"]["25_to_50"]},
                {"Distance": "50-100 mi", "Count": dist_data["buckets"]["50_to_100"]},
                {"Distance": "Over 100 mi", "Count": dist_data["buckets"]["over_100"]},
            ])
            fig = px.bar(
                bucket_df, x="Distance", y="Count",
                title=f"Travel Distance (from {event_city}, {event_state})",
                color_discrete_sequence=[OUTSIDE_COLORS["primary"]],
            )
            fig.update_layout(paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)

    # Geographic map
    geo = analytics.get_geographic_distribution()
    if not geo.empty:
        st.subheader("Participant Origins")
        fig = go.Figure()
        fig.add_trace(go.Scattergeo(
            lat=geo["Latitude"],
            lon=geo["Longitude"],
            mode="markers",
            marker=dict(size=4, color=OUTSIDE_COLORS["primary"], opacity=0.6),
            name="Participants",
        ))
        if event_lat and event_lon:
            fig.add_trace(go.Scattergeo(
                lat=[event_lat],
                lon=[event_lon],
                mode="markers",
                marker=dict(size=14, color=OUTSIDE_COLORS["secondary"], symbol="star"),
                name="Event Location",
            ))
        fig.update_geos(scope="usa", showland=True, landcolor="#F7F7F7",
                        showlakes=True, lakecolor="white")
        fig.update_layout(paper_bgcolor="white", margin=dict(l=0, r=0, t=30, b=0), height=400)
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Page 2: Retention
# ---------------------------------------------------------------------------
def render_retention():
    st.title("Retention Analysis")

    if st.session_state.df is None or st.session_state.df.empty:
        st.warning("No data available. Please select an event series.")
        return

    df = st.session_state.df
    analytics = st.session_state.analytics

    years = sorted(df["event_year"].dropna().unique().astype(int), reverse=True)
    if len(years) < 2:
        st.info("Need at least 2 years of data for retention analysis.")
        return

    year = st.selectbox("Year", years, index=0)
    seg = analytics.get_retention_segments(year)

    # Metric cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Returning", f"{seg['returning']:,}", f"{seg['returning_pct']}%")
    c2.metric("First-Time", f"{seg['first_time']:,}", f"{seg['first_time_pct']}%")
    c3.metric("Lapsed Reactivated", f"{seg['lapsed_reactivated']:,}", f"{seg['lapsed_reactivated_pct']}%")

    # Retention trend (stacked bar)
    trend = analytics.get_retention_trend()
    if not trend.empty:
        st.subheader("Retention Composition Over Time")
        trend_long = trend.melt(
            id_vars=["year"],
            value_vars=["returning", "first_time", "lapsed_reactivated"],
            var_name="segment",
            value_name="count",
        )
        label_map = {"returning": "Returning", "first_time": "First-Time", "lapsed_reactivated": "Lapsed Reactivated"}
        trend_long["segment"] = trend_long["segment"].map(label_map)

        fig = px.bar(
            trend_long, x="year", y="count", color="segment",
            barmode="stack",
            color_discrete_sequence=[OUTSIDE_COLORS["primary"], "#666666", "#CCCCCC"],
        )
        fig.update_layout(
            paper_bgcolor="white", xaxis_title="Year", yaxis_title="Participants",
            legend_title="Segment",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Retention rate trend line
    st.subheader("Year-over-Year Retention Rate")
    retention_rates = []
    for y in sorted(years):
        if y > min(years):
            retention_rates.append({"year": y, "retention_rate": analytics.get_retention_rate(y)})
    if retention_rates:
        rate_df = pd.DataFrame(retention_rates)
        fig = px.line(
            rate_df, x="year", y="retention_rate",
            markers=True,
            color_discrete_sequence=[OUTSIDE_COLORS["primary"]],
        )
        fig.update_layout(
            paper_bgcolor="white", xaxis_title="Year",
            yaxis_title="Retention Rate (%)", yaxis_range=[0, 100],
        )
        st.plotly_chart(fig, use_container_width=True)

    # Cohort retention heatmap
    st.subheader("Cohort Retention Heatmap")
    retention_df = analytics.get_cohort_retention()
    if not retention_df.empty:
        display_df = retention_df.set_index("cohort_year")
        year_cols = [c for c in display_df.columns if c.startswith("year_")]
        if year_cols:
            heatmap_data = display_df[year_cols].values
            safe_data = np.nan_to_num(heatmap_data, nan=0)
            formatted = np.char.add(safe_data.astype(int).astype(str), "%")
            text_data = np.where(np.isnan(heatmap_data), "", formatted)
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=[f"Year {i}" for i in range(len(year_cols))],
                y=display_df.index.astype(str),
                colorscale=[[0, "#FFFFFF"], [0.3, "#FFF3B0"], [0.6, "#FFD100"], [1, "#E6BC00"]],
                text=text_data,
                texttemplate="%{text}",
                textfont={"size": 10, "color": "#000000"},
                hoverongaps=False,
            ))
            fig.update_layout(
                xaxis_title="Years Since First Participation",
                yaxis_title="Cohort Start Year",
                paper_bgcolor="white", plot_bgcolor="white",
            )
            st.plotly_chart(fig, use_container_width=True)

    # AI insight
    try:
        insight = generate_dashboard_insight({
            "retention_segments": {k: v for k, v in seg.items() if k != "participants"},
            "retention_rate": analytics.get_retention_rate(year),
            "year": year,
        })
        st.markdown(f'<div class="insight-box"><strong>AI Insight:</strong> {insight}</div>',
                    unsafe_allow_html=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Page 3: Segment Builder
# ---------------------------------------------------------------------------
def render_segment_builder():
    st.title("Segment Builder")
    st.caption("Filter participants by demographics, behavior, and geography to identify high-value segments.")

    if st.session_state.df is None or st.session_state.df.empty:
        st.warning("No data available. Please select an event series.")
        return

    df = st.session_state.df
    analytics = st.session_state.analytics
    event_lat, event_lon, event_city, event_state = st.session_state.event_center

    years = sorted(df["event_year"].dropna().unique().astype(int))
    available_types = sorted(df["EventType"].dropna().unique().tolist())
    # Only show categories with 5+ entries to keep the list manageable
    cat_counts = df["Catagory"].value_counts()
    available_categories = sorted(cat_counts[cat_counts >= 5].index.tolist())
    available_genders = sorted(df["gender"].dropna().unique().tolist())

    with st.form("segment_filters"):
        col1, col2, col3 = st.columns(3)

        with col1:
            age_range = st.slider("Age Range", 5, 85, (5, 85))
            max_distance = st.slider(
                f"Max Distance from {event_city}, {event_state} (mi)",
                0, 500, 500, step=25,
            )
            year_filter = st.multiselect("Years", years, default=[])

        with col2:
            gender_filter = st.multiselect("Gender", available_genders, default=[])
            attendance_range = st.slider("Attendance Count", 1, 20, (1, 20))

        with col3:
            type_filter = st.multiselect("Event Types", available_types, default=[])
            category_filter = st.multiselect("Categories", available_categories, default=[])

        submitted = st.form_submit_button("Apply Filters", type="primary")

    if not submitted and "segment_result" not in st.session_state:
        st.info("Configure filters above and click **Apply Filters** to build a segment.")
        return

    if submitted:
        st.session_state.segment_result = analytics.get_filtered_segment(
            age_range=age_range if age_range != (5, 85) else None,
            genders=gender_filter or None,
            event_types=type_filter or None,
            max_distance_miles=max_distance if max_distance < 500 else None,
            event_lat=event_lat,
            event_lon=event_lon,
            min_attendance=attendance_range[0] if attendance_range[0] > 1 else None,
            max_attendance=attendance_range[1] if attendance_range[1] < 20 else None,
            years=year_filter or None,
            categories=category_filter or None,
        )

    segment = st.session_state.segment_result
    count = segment["count"]
    pct = segment["pct_of_total"]
    demographics = segment["demographics"]

    st.markdown("---")
    st.subheader(f"Found {count:,} participants ({pct}% of total)")

    if count == 0:
        st.info("No participants match these filters. Try broadening your criteria.")
        return

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Segment Size", f"{count:,}")
    c2.metric("Median Age", f"{demographics.get('median_age', 0):.0f}" if demographics.get("median_age") else "N/A")
    c3.metric("Avg Attendance", f"{demographics.get('avg_attendance', 0):.1f}")
    c4.metric("Avg Distance", f"{demographics.get('avg_distance', 0):.0f} mi" if demographics.get("avg_distance") else "N/A")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        seg_df = segment["participants"]
        valid_ages = seg_df["age"].dropna()
        if len(valid_ages) > 0:
            bins = [0, 18, 25, 35, 45, 55, 65, 100]
            labels = ["Under 18", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
            age_groups = pd.cut(valid_ages, bins=bins, labels=labels)
            age_counts = age_groups.value_counts().sort_index()
            fig = px.bar(
                x=age_counts.index, y=age_counts.values,
                title="Segment Age Distribution",
                color_discrete_sequence=[OUTSIDE_COLORS["primary"]],
            )
            fig.update_layout(paper_bgcolor="white", xaxis_title="Age Group", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        gender_split = demographics.get("gender_split", {})
        if gender_split:
            gender_df = pd.DataFrame([
                {"Gender": k, "Count": v} for k, v in gender_split.items() if v > 0
            ])
            fig = px.pie(
                gender_df, values="Count", names="Gender",
                title="Segment Gender Split",
                color_discrete_sequence=CHART_COLORS,
            )
            fig.update_layout(paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)

    # Participant table
    st.subheader("Participants")
    display_cols = ["first_name", "last_name", "age", "gender", "events_attended"]
    st.dataframe(
        segment["participants"][display_cols].reset_index(drop=True),
        use_container_width=True,
        height=400,
    )

    # Actions
    col1, col2 = st.columns(2)
    with col1:
        csv = segment["participants"][display_cols].to_csv(index=False)
        st.download_button(
            "Download Segment CSV",
            data=csv,
            file_name="segment_export.csv",
            mime="text/csv",
        )
    with col2:
        if st.button("Generate Pitch for This Segment", type="primary"):
            # Build a mini audience profile from the segment
            events = get_promoter_events(st.session_state.promoter_id)
            event_name = events["EventName"].iloc[0] if not events.empty else "Event"

            seg_profile = {
                "total_unique_participants": count,
                "pct_of_total_audience": pct,
                "median_age": demographics.get("median_age"),
                "gender_split": demographics.get("gender_split", {}),
                "avg_attendance": demographics.get("avg_attendance"),
                "avg_distance_miles": demographics.get("avg_distance"),
            }

            # Describe the active filters
            filters_desc = []
            if age_range != (5, 85):
                filters_desc.append(f"ages {age_range[0]}-{age_range[1]}")
            if gender_filter:
                filters_desc.append(f"gender: {', '.join(gender_filter)}")
            if type_filter:
                filters_desc.append(f"event types: {', '.join(type_filter)}")
            if max_distance < 500:
                filters_desc.append(f"within {max_distance} miles")
            if attendance_range != (1, 20):
                filters_desc.append(f"{attendance_range[0]}-{attendance_range[1]} events attended")

            segment_label = f"{event_name} - {', '.join(filters_desc)}" if filters_desc else event_name

            with st.spinner("Generating pitch..."):
                try:
                    pitch = generate_sponsor_pitch(seg_profile, segment_label)
                    st.markdown("---")
                    st.markdown(pitch)
                except Exception as e:
                    st.error(f"Could not generate pitch: {e}")


# ---------------------------------------------------------------------------
# Page 4: YoY Trends
# ---------------------------------------------------------------------------
def render_yoy_trends():
    st.title("Year-over-Year Trends")

    if st.session_state.df is None or st.session_state.df.empty:
        st.warning("No data available. Please select an event series.")
        return

    df = st.session_state.df
    analytics = st.session_state.analytics

    years = sorted(df["event_year"].dropna().unique().astype(int), reverse=True)
    if len(years) < 2:
        st.info("Need at least 2 years of data for trend analysis.")
        return

    # Year comparison selectors
    col1, col2 = st.columns(2)
    with col1:
        year2 = st.selectbox("Current Year", years, index=0)
    with col2:
        prior_years = [y for y in years if y < year2]
        year1 = st.selectbox("Compare To", prior_years, index=0 if prior_years else None)

    if not year1:
        return

    yoy = analytics.get_yoy_metrics(year1, year2)
    metrics = yoy["metrics"]

    # Metric cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Participants",
        f"{metrics['total_participants'][year2]:,}",
        f"{metrics['total_participants']['change_pct']:+.1f}%",
    )
    c2.metric(
        "Revenue",
        f"${metrics['revenue'][year2]:,.0f}",
        f"{metrics['revenue']['change_pct']:+.1f}%",
    )
    c3.metric(
        "Returning",
        f"{metrics['returning']['count']:,}",
        f"{metrics['returning']['pct_of_year1']}% of {year1}",
    )
    c4.metric(
        "New Participants",
        f"{metrics['new']['count']:,}",
        f"{metrics['new']['pct_of_year2']}% of {year2}",
    )

    # Participant count trend (all years)
    st.subheader("Participant Count Trend")
    all_years_sorted = sorted(df["event_year"].dropna().unique().astype(int))
    yearly_counts = [
        {"year": y, "participants": df[df["event_year"] == y]["participant_id"].nunique()}
        for y in all_years_sorted
    ]
    fig = px.line(
        pd.DataFrame(yearly_counts), x="year", y="participants",
        markers=True,
        color_discrete_sequence=[OUTSIDE_COLORS["primary"]],
    )
    fig.update_layout(paper_bgcolor="white", xaxis_title="Year", yaxis_title="Unique Participants")
    st.plotly_chart(fig, use_container_width=True)

    # Demographic shifts
    demo_trend = analytics.get_demographic_trend()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Age Distribution Shift")
        age_df = demo_trend["age_by_year"]
        if not age_df.empty:
            compare_ages = age_df[age_df["year"].isin([year1, year2])].copy()
            compare_ages["year"] = compare_ages["year"].astype(str)
            fig = px.bar(
                compare_ages, x="age_group", y="pct", color="year",
                barmode="group",
                color_discrete_sequence=[OUTSIDE_COLORS["accent"], OUTSIDE_COLORS["primary"]],
            )
            fig.update_layout(paper_bgcolor="white", xaxis_title="", yaxis_title="% of Participants")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Gender Composition Shift")
        gender_df = demo_trend["gender_by_year"]
        if not gender_df.empty:
            compare_gender = gender_df[gender_df["year"].isin([year1, year2])].copy()
            compare_gender["year"] = compare_gender["year"].astype(str)
            fig = px.bar(
                compare_gender, x="gender", y="pct", color="year",
                barmode="group",
                color_discrete_sequence=[OUTSIDE_COLORS["accent"], OUTSIDE_COLORS["primary"]],
            )
            fig.update_layout(paper_bgcolor="white", xaxis_title="", yaxis_title="% of Participants")
            st.plotly_chart(fig, use_container_width=True)

    # Median age trend
    median_df = demo_trend["median_age_by_year"]
    if not median_df.empty:
        st.subheader("Median Age Trend")
        fig = px.line(
            median_df, x="year", y="median_age",
            markers=True,
            color_discrete_sequence=[OUTSIDE_COLORS["primary"]],
        )
        fig.update_layout(paper_bgcolor="white", xaxis_title="Year", yaxis_title="Median Age")
        st.plotly_chart(fig, use_container_width=True)

    # Category performance table
    st.subheader(f"Category Performance ({year2})")
    cat_perf = analytics.get_category_performance(year2)
    if not cat_perf.empty:
        display_cols = ["category", "participants", "total_revenue", "avg_fee"]
        if "yoy_growth" in cat_perf.columns:
            display_cols.append("yoy_growth")
        st.dataframe(cat_perf[display_cols], use_container_width=True)

    # AI insight
    try:
        insight = generate_dashboard_insight(metrics)
        st.markdown(f'<div class="insight-box"><strong>AI Insight:</strong> {insight}</div>',
                    unsafe_allow_html=True)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Page 5: Sponsor Pitch
# ---------------------------------------------------------------------------
def render_sponsor_pitch():
    st.title("Sponsor Pitch Generator")
    st.caption("Generate a data-driven audience profile to include in sponsor pitch decks.")

    if st.session_state.df is None or st.session_state.df.empty:
        st.warning("No data available. Please select an event series.")
        return

    analytics = st.session_state.analytics
    event_lat, event_lon, event_city, event_state = st.session_state.event_center

    events = get_promoter_events(st.session_state.promoter_id)
    event_name = events["EventName"].iloc[0] if not events.empty else "Event"

    # Key stats cards
    profile = analytics.get_audience_profile(event_lat=event_lat, event_lon=event_lon)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Participants", f"{profile.get('total_unique_participants', 0):,}")
    c2.metric("Retention Rate", f"{profile.get('retention_rate', 0):.0f}%" if profile.get("retention_rate") else "N/A")
    c3.metric("Median Age", f"{profile.get('median_age', 0):.0f}" if profile.get("median_age") else "N/A")

    geo = profile.get("geographic", {})
    c4.metric("Avg Distance", f"{geo.get('avg_miles', 0):.0f} mi" if geo else "N/A")

    # Mini charts
    col1, col2 = st.columns(2)

    with col1:
        age_data = profile.get("age_distribution", [])
        if age_data:
            age_df = pd.DataFrame(age_data)
            fig = px.pie(
                age_df, values="count", names="age_group",
                title="Age Distribution",
                color_discrete_sequence=CHART_COLORS,
            )
            fig.update_layout(paper_bgcolor="white", height=300)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        loyalty = profile.get("loyalty_cohorts", {})
        if loyalty and loyalty.get("total", 0) > 0:
            loyalty_df = pd.DataFrame([
                {"Cohort": "One-Timers", "Count": loyalty["one_timers"]},
                {"Cohort": "Regulars (2-3x)", "Count": loyalty["regulars"]},
                {"Cohort": "Super Fans (4+)", "Count": loyalty["super_fans"]},
            ])
            fig = px.pie(
                loyalty_df, values="Count", names="Cohort",
                title="Loyalty Distribution",
                color_discrete_sequence=["#666666", "#333333", "#FFD100"],
            )
            fig.update_layout(paper_bgcolor="white", height=300)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Generation controls
    col1, col2 = st.columns([1, 3])
    with col1:
        tone = st.radio("Tone", ["Professional", "Casual"], index=0)
    with col2:
        generate = st.button("Generate Audience Profile", type="primary")

    if generate:
        with st.spinner("Generating sponsor pitch..."):
            try:
                pitch = generate_sponsor_pitch(profile, event_name, tone=tone.lower())
                st.markdown("---")
                st.markdown(pitch)

                # Download button
                st.download_button(
                    "Download as Markdown",
                    data=pitch,
                    file_name=f"{event_name.replace(' ', '_')}_audience_profile.md",
                    mime="text/markdown",
                )
            except Exception as e:
                st.error(f"Could not generate pitch: {e}")

    # Raw data expander
    with st.expander("View Raw Audience Data"):
        st.json(json.loads(json.dumps(profile, default=str)))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    init_session_state()
    page = render_sidebar()

    if page == "Audience Profile":
        render_demographics()
    elif page == "Retention":
        render_retention()
    elif page == "Segment Builder":
        render_segment_builder()
    elif page == "YoY Trends":
        render_yoy_trends()
    elif page == "Sponsor Pitch":
        render_sponsor_pitch()


if __name__ == "__main__":
    main()
