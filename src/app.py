"""
Event Director Analytics Demo - Streamlit App

AI-powered insights for race directors.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

from data_loader import (
    load_enriched_entries,
    get_promoter_ids,
    get_promoter_data,
    get_promoter_events,
    get_promoter_summary,
)
from analytics import EventAnalytics, EcosystemBenchmark
from llm_client import (
    generate_dashboard_insight,
    generate_query_response,
    generate_reengagement_message,
    translate_natural_query,
)


# Page config
st.set_page_config(
    page_title="Event Director Analytics",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Outside Brand Colors
OUTSIDE_COLORS = {
    "primary": "#FFD100",        # Signature yellow
    "primary_dark": "#E6BC00",
    "primary_light": "#FFF3B0",
    "secondary": "#000000",      # Black
    "secondary_light": "#1a1a1a",
    "accent": "#333333",
    "text": "#000000",
    "text_light": "#555555",
    "text_muted": "#666666",
    "bg": "#F7F7F7",
    "card_bg": "#FFFFFF",
    "warm_bg": "#fffbea",
}

# Chart color sequence for Plotly (Outside brand)
OUTSIDE_CHART_COLORS = [
    "#FFD100",  # Primary yellow
    "#000000",  # Black
    "#333333",  # Dark gray
    "#666666",  # Medium gray
    "#999999",  # Light gray
    "#E6BC00",  # Dark gold
    "#B8960A",  # Bronze
    "#CCCCCC",  # Lighter gray
]

# Custom CSS with Outside brand styling
st.markdown("""
<style>
    /* Outside Brand Styling */
    .stApp {
        background-color: #F7F7F7;
    }

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

    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #E6BC00;
        padding: 15px;
        margin: 15px 0;
        border-radius: 0 12px 12px 0;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #000000;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: #FFFFFF;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #FFD100 !important;
    }

    [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stSelectbox label {
        color: #FFFFFF !important;
    }

    /* Sidebar navigation radio buttons - make text visible */
    [data-testid="stSidebar"] .stRadio label {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stRadio p {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
    }

    /* Primary button styling */
    .stButton > button[kind="primary"] {
        background-color: #FFD100;
        color: #000000;
        border: none;
        font-weight: 600;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #E6BC00;
        color: #000000;
    }

    /* Regular button styling */
    .stButton > button {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
    }

    .stButton > button:hover {
        border-color: #FFD100;
        background-color: #fffbea;
    }

    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #000000;
    }

    [data-testid="stMetricDelta"] svg {
        stroke: #FFD100;
    }

    /* Headers */
    h1, h2, h3 {
        color: #000000;
    }

    /* Card-like containers */
    [data-testid="stExpander"] {
        border: 1px solid #E0E0E0;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "promoter_id" not in st.session_state:
        st.session_state.promoter_id = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "df" not in st.session_state:
        st.session_state.df = None
    if "analytics" not in st.session_state:
        st.session_state.analytics = None


def render_sidebar():
    """Render sidebar with promoter selection and navigation."""
    with st.sidebar:
        st.title("🏃 Event Director Analytics")
        st.markdown("---")

        # Promoter selection
        st.subheader("Select Your Events")
        promoters = get_promoter_ids()

        # Format options
        options = {f"{name} ({count} events)": pid for pid, name, count in promoters}
        selected = st.selectbox(
            "Event Organizer",
            options=list(options.keys()),
            index=0 if options else None,
        )

        if selected:
            promoter_id = options[selected]
            if promoter_id != st.session_state.promoter_id:
                st.session_state.promoter_id = promoter_id
                st.session_state.df = get_promoter_data(promoter_id)
                st.session_state.analytics = EventAnalytics(st.session_state.df)
                st.session_state.chat_history = []

        st.markdown("---")

        # Navigation
        st.subheader("Navigation")
        page = st.radio(
            "Go to",
            options=[
                "📊 Smart Dashboard",
                "💬 Ask Questions",
                "👥 Loyalty & Churn",
                "🏆 Benchmarking",
                "🗺️ Geographic View",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.caption("Powered by AI")

        return page


def render_dashboard():
    """Render the Smart Dashboard screen."""
    st.title("📊 Smart Dashboard")

    if st.session_state.df is None or st.session_state.df.empty:
        st.warning("No data available. Please select an event organizer.")
        return

    df = st.session_state.df
    analytics = st.session_state.analytics

    # Get available years
    years = sorted(df["event_year"].dropna().unique().astype(int), reverse=True)

    if len(years) < 2:
        st.info("Need at least 2 years of data for year-over-year comparison.")
        return

    # Year selection
    col1, col2 = st.columns(2)
    with col1:
        year2 = st.selectbox("Current Year", years, index=0)
    with col2:
        prior_years = [y for y in years if y < year2]
        year1 = st.selectbox("Compare To", prior_years, index=0) if prior_years else None

    if year1 is None:
        st.info("No prior year data available for comparison.")
        return

    # YoY Metrics
    st.subheader("Year-over-Year Comparison")
    yoy = analytics.get_yoy_metrics(year1, year2)
    metrics = yoy["metrics"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        delta = f"{metrics['total_participants']['change_pct']:+.1f}%"
        st.metric(
            "Total Participants",
            metrics["total_participants"][year2],
            delta,
        )

    with col2:
        st.metric(
            "Returning",
            metrics["returning"]["count"],
            f"{metrics['returning']['pct_of_year1']:.0f}% of {year1}",
        )

    with col3:
        st.metric(
            "New Participants",
            metrics["new"]["count"],
            f"{metrics['new']['pct_of_year2']:.0f}% of {year2}",
        )

    with col4:
        revenue_delta = f"{metrics['revenue']['change_pct']:+.1f}%"
        st.metric(
            "Revenue",
            f"${metrics['revenue'][year2]:,.0f}",
            revenue_delta,
        )

    # AI Insight
    with st.spinner("Generating insight..."):
        insight = generate_dashboard_insight({
            "year_comparison": f"{year1} vs {year2}",
            "participant_change": metrics["total_participants"]["change_pct"],
            "returning_pct": metrics["returning"]["pct_of_year1"],
            "new_pct": metrics["new"]["pct_of_year2"],
            "revenue_change": metrics["revenue"]["change_pct"],
        })

    st.markdown(f"""
    <div class="insight-box">
        <strong>💡 AI Insight:</strong> {insight}
    </div>
    """, unsafe_allow_html=True)

    # Category Performance
    st.subheader("Category Performance")

    cat_perf = analytics.get_category_performance(year2)
    if not cat_perf.empty:
        # Top categories chart
        top_cats = cat_perf.head(10)

        fig = px.bar(
            top_cats,
            x="category",
            y="participants",
            color="total_revenue",
            title=f"Top 10 Categories by Participation ({year2})",
            labels={"participants": "Participants", "total_revenue": "Revenue ($)", "category": "Category"},
            color_continuous_scale=[[0, "#333333"], [0.5, "#FFD100"], [1, "#E6BC00"]],
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=500,
            margin=dict(b=150),  # More space for long category labels
            coloraxis_colorbar=dict(
                title="Revenue ($)",
                tickprefix="$",
                tickformat=",",
                len=0.7,
            ),
            xaxis=dict(
                tickfont=dict(size=10),
            ),
        )
        fig.update_traces(marker_line_color="#000000", marker_line_width=1)
        st.plotly_chart(fig, use_container_width=True)

        # Category table
        with st.expander("View All Categories"):
            st.dataframe(
                cat_perf[["category", "participants", "total_revenue", "avg_fee", "yoy_growth"]],
                use_container_width=True,
            )

    # Demographics
    st.subheader("Participant Demographics")

    col1, col2 = st.columns(2)

    with col1:
        age_dist = analytics.get_age_distribution(year2)
        if not age_dist.empty:
            fig = px.pie(
                age_dist,
                values="count",
                names="age_group",
                title="Age Distribution",
                color_discrete_sequence=OUTSIDE_CHART_COLORS,
            )
            fig.update_layout(paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        gender_dist = analytics.get_gender_distribution(year2)
        if gender_dist:
            fig = px.pie(
                values=list(gender_dist.values()),
                names=list(gender_dist.keys()),
                title="Gender Distribution",
                color_discrete_sequence=OUTSIDE_CHART_COLORS,
            )
            fig.update_layout(paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)


def render_chat():
    """Render the Chat Interface screen."""
    st.title("💬 Ask Questions About Your Data")

    if st.session_state.df is None or st.session_state.df.empty:
        st.warning("No data available. Please select an event organizer.")
        return

    df = st.session_state.df

    # Initialize query state
    if "query_input" not in st.session_state:
        st.session_state.query_input = ""
    if "run_query" not in st.session_state:
        st.session_state.run_query = False

    # Example questions
    st.markdown("**Example questions you can ask:**")
    examples = [
        "Give me participants who attended 3+ times but haven't registered this year",
        "Who are my top 5 most loyal participants?",
        "What's my retention rate compared to last year?",
        "Which category has the highest retention?",
        "How many participants come from more than 100 miles away?",
        "What's the age distribution in my Masters categories?",
    ]

    def set_example_query(example_text):
        # Set the query_input key directly (this is what text_input reads from)
        st.session_state.query_input = example_text
        st.session_state.run_query = True

    cols = st.columns(2)
    for i, example in enumerate(examples):
        with cols[i % 2]:
            st.button(example, key=f"example_{i}", on_click=set_example_query, args=(example,))

    st.markdown("---")

    # Query input - uses key="query_input" so it reads/writes to st.session_state.query_input
    query = st.text_input(
        "Ask a question about your event data:",
        key="query_input",
    )

    # Run query if button clicked or example selected
    run_search = st.button("🔍 Search", type="primary")
    should_run = (run_search and query) or (st.session_state.run_query and query)

    if should_run:
        st.session_state.run_query = False  # Reset flag
        with st.spinner("Analyzing your data..."):
            try:
                # Build schema context for LLM
                schema_context = f"""
Columns: {', '.join(df.columns.tolist())}

Sample data (first 3 rows):
{df.head(3).to_string()}

Key columns:
- participant_id: Unique participant identifier (FName|LName|DOB)
- event_year: Year of the event
- EventDate: Date of event
- Catagory: Race category name
- EntryFee: Registration fee
- FName, LName: Participant name
- participant_age: Age at event
- gender: M/F
- Latitude, Longitude: Participant location
"""

                # Translate query to pandas code
                code = translate_natural_query(query, schema_context)

                st.code(code, language="python")

                # Execute query safely with allowed modules
                import math
                safe_builtins = {
                    "len": len, "sum": sum, "min": min, "max": max,
                    "abs": abs, "round": round, "sorted": sorted,
                    "list": list, "dict": dict, "set": set, "tuple": tuple,
                    "str": str, "int": int, "float": float, "bool": bool,
                    "range": range, "enumerate": enumerate, "zip": zip,
                    "map": map, "filter": filter, "any": any, "all": all,
                    "print": print,
                }
                exec_globals = {
                    "__builtins__": safe_builtins,
                    "pd": pd,
                    "np": np,
                    "math": math,
                }
                local_vars = {"df": df}
                exec(code, exec_globals, local_vars)
                result = local_vars.get("result")

                if result is not None:
                    # Display results
                    st.subheader("Results")

                    if isinstance(result, pd.DataFrame):
                        st.dataframe(result, use_container_width=True)

                        # Export option
                        csv = result.to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV",
                            csv,
                            "query_results.csv",
                            "text/csv",
                        )
                    elif isinstance(result, pd.Series):
                        st.dataframe(result.to_frame(), use_container_width=True)
                    else:
                        st.write(result)

                    # Generate natural language response
                    response = generate_query_response(
                        query,
                        str(result.head(20) if isinstance(result, (pd.DataFrame, pd.Series)) else result),
                        f"DataFrame with {len(df)} entries, {df['participant_id'].nunique()} unique participants"
                    )

                    st.markdown(f"""
                    <div class="insight-box">
                        <strong>💡 Summary:</strong> {response}
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error executing query: {str(e)}")
                st.info("Try rephrasing your question or check the example queries above.")


def render_loyalty():
    """Render the Loyalty & Churn Analysis screen."""
    st.title("👥 Loyalty & Churn Intelligence")

    if st.session_state.df is None or st.session_state.df.empty:
        st.warning("No data available. Please select an event organizer.")
        return

    analytics = st.session_state.analytics
    df = st.session_state.df

    # Loyalty Cohorts
    st.subheader("Loyalty Cohorts")

    cohorts = analytics.get_loyalty_cohorts()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("One-Timers", cohorts["one_timers"], help="Attended exactly once")
    with col2:
        st.metric("Regulars", cohorts["regulars"], help="Attended 2-3 times")
    with col3:
        st.metric("Super Fans", cohorts["super_fans"], help="Attended 4+ times")
    with col4:
        st.metric("Total Unique", cohorts["total"])

    # Cohort visualization
    cohort_data = {
        "Cohort": ["One-Timers", "Regulars (2-3x)", "Super Fans (4+)"],
        "Count": [cohorts["one_timers"], cohorts["regulars"], cohorts["super_fans"]],
    }
    fig = px.pie(
        cohort_data,
        values="Count",
        names="Cohort",
        title="Participant Loyalty Distribution",
        color_discrete_sequence=["#666666", "#333333", "#FFD100"],  # Outside brand: gray to yellow for loyalty
    )
    fig.update_layout(paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

    # Cohort Retention Table
    st.subheader("Cohort Retention Analysis")

    retention_df = analytics.get_cohort_retention()
    if not retention_df.empty:
        # Format for display
        display_df = retention_df.copy()
        display_df = display_df.set_index("cohort_year")

        # Create heatmap
        year_cols = [c for c in display_df.columns if c.startswith("year_")]
        if year_cols:
            heatmap_data = display_df[year_cols].values

            # Create custom text that shows empty string for NaN values
            text_data = np.where(
                np.isnan(heatmap_data),
                "",
                np.char.add(np.round(heatmap_data, 0).astype(int).astype(str), "%")
            )

            # Outside brand colorscale: white -> yellow -> dark gold
            outside_colorscale = [
                [0, "#FFFFFF"],
                [0.3, "#FFF3B0"],
                [0.6, "#FFD100"],
                [1, "#E6BC00"],
            ]

            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=[f"Year {i}" for i in range(len(year_cols))],
                y=display_df.index.astype(str),
                colorscale=outside_colorscale,
                text=text_data,
                texttemplate="%{text}",
                textfont={"size": 10, "color": "#000000"},
                hoverongaps=False,
            ))
            fig.update_layout(
                title="Cohort Retention Over Time",
                xaxis_title="Years Since First Participation",
                yaxis_title="Cohort Start Year",
                paper_bgcolor="white",
                plot_bgcolor="white",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Top Participants (VIPs)
    st.subheader("🏆 Top Participants (VIPs)")

    top_participants = analytics.get_top_participants(10)
    if not top_participants.empty:
        st.dataframe(
            top_participants[[
                "first_name", "last_name", "events_attended",
                "years_attended", "total_spent"
            ]],
            use_container_width=True,
        )

    # Churn List
    st.subheader("⚠️ Churn Risk: Lapsed Participants")

    years = sorted(df["event_year"].dropna().unique().astype(int), reverse=True)
    current_year = years[0] if years else datetime.now().year

    col1, col2 = st.columns(2)
    with col1:
        check_year = st.selectbox("Check absences for year:", years[:3] if len(years) >= 3 else years)
    with col2:
        min_attendance = st.slider("Minimum prior attendance:", 1, 5, 2)

    churn_list = analytics.get_churn_list(check_year, min_attendance)

    if not churn_list.empty:
        st.write(f"Found **{len(churn_list)}** participants who attended {min_attendance}+ times but not in {check_year}")

        st.dataframe(
            churn_list[[
                "first_name", "last_name", "times_attended",
                "years_attended", "last_category"
            ]].head(20),
            use_container_width=True,
        )

        # Re-engagement message generator
        st.subheader("📧 Generate Re-engagement Message")

        if st.button("Generate Sample Message"):
            sample = churn_list.iloc[0]
            name = f"{sample['first_name']} {sample['last_name']}"

            with st.spinner("Generating personalized message..."):
                message = generate_reengagement_message(
                    name,
                    sample["last_category"],
                    sample["years_attended"],
                )

            st.markdown(f"""
            <div class="insight-box">
                <strong>To: {name}</strong><br><br>
                {message}
            </div>
            """, unsafe_allow_html=True)

        # Export option
        csv = churn_list.to_csv(index=False)
        st.download_button(
            "📥 Download Full Churn List",
            csv,
            "churn_list.csv",
            "text/csv",
        )
    else:
        st.success("No churned participants found with the selected criteria!")


def render_benchmarking():
    """Render the Ecosystem Benchmarking screen."""
    st.title("🏆 Ecosystem Benchmarking")

    if st.session_state.df is None or st.session_state.df.empty:
        st.warning("No data available. Please select an event organizer.")
        return

    promoter_id = st.session_state.promoter_id
    promoter_df = st.session_state.df

    # Load full dataset for comparison
    with st.spinner("Loading ecosystem data..."):
        all_df = load_enriched_entries()
        benchmark = EcosystemBenchmark(all_df)

    # Filter options
    st.subheader("Comparison Filters")

    col1, col2 = st.columns(2)

    with col1:
        event_types = promoter_df["EventType"].dropna().unique().tolist()
        selected_type = st.selectbox(
            "Event Type",
            ["All Types"] + event_types,
        )
        event_type = None if selected_type == "All Types" else selected_type

    with col2:
        states = all_df["EventState"].dropna().unique().tolist()
        selected_state = st.selectbox(
            "State",
            ["All States"] + sorted(states),
        )
        state = None if selected_state == "All States" else selected_state

    # Get benchmark metrics
    metrics = benchmark.get_benchmark_metrics(promoter_id, event_type, state)

    # Display comparison
    st.subheader("Your Events vs. Ecosystem")

    col1, col2, col3, col4 = st.columns(4)

    your_metrics = metrics["your_event"]
    comp_metrics = metrics["comparison"]

    with col1:
        diff = your_metrics["avg_entry_fee"] - comp_metrics["avg_entry_fee"]
        st.metric(
            "Avg Entry Fee",
            f"${your_metrics['avg_entry_fee']:.2f}",
            f"${diff:+.2f} vs avg",
        )

    with col2:
        diff = your_metrics["retention_rate"] - comp_metrics["retention_rate"]
        st.metric(
            "Retention Rate",
            f"{your_metrics['retention_rate']:.1f}%",
            f"{diff:+.1f}% vs avg",
        )

    with col3:
        diff = your_metrics["yoy_growth"] - comp_metrics["yoy_growth"]
        st.metric(
            "YoY Growth",
            f"{your_metrics['yoy_growth']:+.1f}%",
            f"{diff:+.1f}% vs avg",
        )

    with col4:
        st.metric(
            "Categories Offered",
            your_metrics["total_categories"],
            f"Avg: {comp_metrics['avg_categories']:.1f}",
        )

    st.caption(f"Compared against {comp_metrics['num_events_compared']} other event organizers")

    # Benchmark table
    st.subheader("Detailed Comparison")

    comparison_data = {
        "Metric": ["Average Entry Fee", "Retention Rate", "YoY Growth", "Number of Categories"],
        "Your Events": [
            f"${your_metrics['avg_entry_fee']:.2f}",
            f"{your_metrics['retention_rate']:.1f}%",
            f"{your_metrics['yoy_growth']:+.1f}%",
            your_metrics["total_categories"],
        ],
        "Ecosystem Average": [
            f"${comp_metrics['avg_entry_fee']:.2f}",
            f"{comp_metrics['retention_rate']:.1f}%",
            f"{comp_metrics['yoy_growth']:+.1f}%",
            f"{comp_metrics['avg_categories']:.1f}",
        ],
    }

    st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)

    # AI Insight
    insight_data = {
        "your_fee_vs_avg": f"{((your_metrics['avg_entry_fee'] / comp_metrics['avg_entry_fee']) - 1) * 100:.0f}% {'above' if your_metrics['avg_entry_fee'] > comp_metrics['avg_entry_fee'] else 'below'}" if comp_metrics['avg_entry_fee'] > 0 else "N/A",
        "retention_percentile": "above average" if your_metrics['retention_rate'] > comp_metrics['retention_rate'] else "below average",
        "growth_comparison": "outpacing" if your_metrics['yoy_growth'] > comp_metrics['yoy_growth'] else "trailing",
    }

    with st.spinner("Generating insight..."):
        insight = generate_dashboard_insight({
            "benchmark_comparison": insight_data,
            "your_metrics": your_metrics,
            "ecosystem_metrics": comp_metrics,
        })

    st.markdown(f"""
    <div class="insight-box">
        <strong>💡 AI Insight:</strong> {insight}
    </div>
    """, unsafe_allow_html=True)

    # Participant Overlap
    st.subheader("🔗 Participant Overlap with Other Events")

    overlap_df = benchmark.get_participant_overlap(promoter_id)
    if not overlap_df.empty:
        st.write("Events that share participants with yours:")
        st.dataframe(
            overlap_df.head(10)[[
                "event_name", "shared_participants", "pct_of_your_base"
            ]],
            use_container_width=True,
        )
    else:
        st.info("No significant participant overlap found with other events.")


def render_geographic():
    """Render the Geographic Intelligence screen."""
    st.title("🗺️ Geographic Intelligence")

    if st.session_state.df is None or st.session_state.df.empty:
        st.warning("No data available. Please select an event organizer.")
        return

    analytics = st.session_state.analytics
    df = st.session_state.df

    # Get event location (use first event as reference)
    events = get_promoter_events(st.session_state.promoter_id)
    if events.empty:
        st.warning("No event location data available.")
        return

    event_lat = events["EventLat"].dropna().iloc[0] if not events["EventLat"].dropna().empty else None
    event_lon = events["EventLon"].dropna().iloc[0] if not events["EventLon"].dropna().empty else None

    # Distance Distribution
    if event_lat and event_lon:
        st.subheader("Travel Distance Distribution")

        distance_data = analytics.get_distance_distribution(event_lat, event_lon)

        if distance_data:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Average Distance", f"{distance_data['avg_miles']:.0f} miles")
            with col2:
                st.metric("Max Distance", f"{distance_data['max_miles']:.0f} miles")
            with col3:
                st.metric("Participants with Location", distance_data["total_with_location"])

            # Distance buckets chart
            buckets = distance_data["buckets"]
            fig = px.bar(
                x=["Under 25 mi", "25-50 mi", "50-100 mi", "100+ mi"],
                y=[buckets["under_25"], buckets["25_to_50"], buckets["50_to_100"], buckets["over_100"]],
                title="Participants by Travel Distance",
                labels={"x": "Distance", "y": "Participants"},
                color_discrete_sequence=["#FFD100"],
            )
            fig.update_traces(marker_line_color="#000000", marker_line_width=1)
            fig.update_layout(paper_bgcolor="white", plot_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)

    # Map visualization
    st.subheader("Participant Origin Map")

    geo_df = analytics.get_geographic_distribution()

    if not geo_df.empty:
        # Use Plotly for stable, non-flickering map
        # Sample with fixed seed for consistency
        np.random.seed(42)
        sample_size = min(500, len(geo_df))
        sample_df = geo_df.sample(n=sample_size, random_state=42)

        # Create scatter map with Plotly (more stable than Folium in Streamlit)
        fig = go.Figure()

        # Add participant locations (Outside brand: dark gray markers)
        fig.add_trace(go.Scattergeo(
            lon=sample_df["Longitude"],
            lat=sample_df["Latitude"],
            mode="markers",
            marker=dict(
                size=6,
                color="#333333",
                opacity=0.7,
            ),
            name="Participants",
            hoverinfo="skip",
        ))

        # Add event location marker (Outside brand: yellow star)
        if event_lat and event_lon:
            fig.add_trace(go.Scattergeo(
                lon=[event_lon],
                lat=[event_lat],
                mode="markers",
                marker=dict(
                    size=18,
                    color="#FFD100",
                    symbol="star",
                    line=dict(color="#000000", width=1),
                ),
                name="Event Location",
                hoverinfo="text",
                hovertext="Event Location",
            ))

        # Center map on event or participant centroid
        center_lat = event_lat if event_lat else sample_df["Latitude"].mean()
        center_lon = event_lon if event_lon else sample_df["Longitude"].mean()

        fig.update_geos(
            scope="north america",
            center=dict(lat=center_lat, lon=center_lon),
            projection_scale=4,
            showland=True,
            landcolor="rgb(243, 243, 243)",
            showocean=True,
            oceancolor="rgb(204, 229, 255)",
            showlakes=True,
            lakecolor="rgb(204, 229, 255)",
            showrivers=True,
            rivercolor="rgb(204, 229, 255)",
            showcountries=True,
            countrycolor="rgb(204, 204, 204)",
            showsubunits=True,
            subunitcolor="rgb(204, 204, 204)",
        )

        fig.update_layout(
            title=f"Participant Origins ({sample_size} shown)",
            height=500,
            margin=dict(l=0, r=0, t=40, b=0),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            paper_bgcolor="white",
        )

        st.plotly_chart(fig, use_container_width=True, key="geo_map")

    else:
        st.info("No geographic data available for participants.")

    # AI Insight
    if event_lat and event_lon and distance_data:
        insight_text = f"Based on the geographic distribution, {distance_data['buckets']['under_25'] + distance_data['buckets']['25_to_50']} participants ({(distance_data['buckets']['under_25'] + distance_data['buckets']['25_to_50']) / distance_data['total_with_location'] * 100:.0f}%) travel less than 50 miles. Consider targeted marketing in metropolitan areas within this radius for potential growth."

        st.markdown(f"""
        <div class="insight-box">
            <strong>💡 AI Insight:</strong> {insight_text}
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main app entry point."""
    init_session_state()
    page = render_sidebar()

    if page == "📊 Smart Dashboard":
        render_dashboard()
    elif page == "💬 Ask Questions":
        render_chat()
    elif page == "👥 Loyalty & Churn":
        render_loyalty()
    elif page == "🏆 Benchmarking":
        render_benchmarking()
    elif page == "🗺️ Geographic View":
        render_geographic()


if __name__ == "__main__":
    main()
