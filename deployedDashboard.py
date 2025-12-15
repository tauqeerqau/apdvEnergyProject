import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt

# ---------------------------------------------------
# Page Config
# ---------------------------------------------------
st.set_page_config(
    page_title="Global Electricity Analysis",
    layout="wide"
)

st.title("🌍 Global Electricity Analysis")

# ---------------------------------------------------
# Load Data (CSV for deployment safety)
# ---------------------------------------------------
@st.cache_data
def load_data():
    return pd.read_csv("integrated_electricity_dataset.csv")

df = load_data()

# ---------------------------------------------------
# Sidebar Filters
# ---------------------------------------------------
st.sidebar.header("Filters")

country = st.sidebar.selectbox(
    "Select Country",
    sorted(df["country_name"].unique())
)

year_range = st.sidebar.slider(
    "Select Year Range",
    int(df["year"].min()),
    int(df["year"].max()),
    (int(df["year"].min()), int(df["year"].max()))
)

# ---------------------------------------------------
# Apply Filters
# ---------------------------------------------------
filtered_df = df[
    (df["country_name"] == country) &
    (df["year"] >= year_range[0]) &
    (df["year"] <= year_range[1])
]

# ---------------------------------------------------
# KPI Metrics
# ---------------------------------------------------
st.subheader("Key Indicators (Selected Filters)")

if not filtered_df.empty:
    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Avg Electricity Use (kWh/capita)",
        f"{filtered_df['electricity_use_kwh_per_capita'].mean():.0f}"
    )

    c2.metric(
        "Avg Renewable Electricity (%)",
        f"{filtered_df['renewable_electricity_percent'].mean():.1f}"
    )

    c3.metric(
        "Avg Electricity Losses (%)",
        f"{filtered_df['electricity_losses_pct'].mean():.1f}"
    )
else:
    st.warning("No data available for selected filters.")

# ---------------------------------------------------
# Line Charts
# ---------------------------------------------------
st.subheader("Electricity Use per Capita Over Time")

if not filtered_df.empty:
    st.line_chart(
        filtered_df.sort_values("year")
        .set_index("year")["electricity_use_kwh_per_capita"]
    )

st.subheader("Renewable Electricity (% of Total) Over Time")

if not filtered_df.empty:
    st.line_chart(
        filtered_df.sort_values("year")
        .set_index("year")["renewable_electricity_percent"]
    )

st.subheader("Electricity Losses (%) Over Time")

if not filtered_df.empty:
    st.line_chart(
        filtered_df.sort_values("year")
        .set_index("year")["electricity_losses_pct"]
    )

# ---------------------------------------------------
# Combined Trend (Altair)
# ---------------------------------------------------
st.subheader("Combined Indexed Trend (Base Year = 100)")

if len(filtered_df) > 1:
    chart_df = filtered_df.sort_values("year").copy()
    base = chart_df.iloc[0]

    chart_df["Electricity Use Index"] = (
        chart_df["electricity_use_kwh_per_capita"]
        / base["electricity_use_kwh_per_capita"] * 100
    )
    chart_df["Renewable Index"] = (
        chart_df["renewable_electricity_percent"]
        / base["renewable_electricity_percent"] * 100
    )
    chart_df["Losses Index"] = (
        chart_df["electricity_losses_pct"]
        / base["electricity_losses_pct"] * 100
    )

    melted = chart_df.melt(
        id_vars="year",
        value_vars=[
            "Electricity Use Index",
            "Renewable Index",
            "Losses Index"
        ],
        var_name="Indicator",
        value_name="Index"
    )

    chart = alt.Chart(melted).mark_line().encode(
        x="year:O",
        y="Index:Q",
        color="Indicator:N",
        tooltip=["year", "Indicator", "Index"]
    )

    st.altair_chart(chart, use_container_width=True)

# ---------------------------------------------------
# World Map (Plotly Choropleth)
# ---------------------------------------------------
st.subheader("🌍 Interactive World Map (Electricity Use per Capita)")

map_year = st.slider(
    "Select Year for Map",
    int(df["year"].min()),
    int(df["year"].max()),
    int(df["year"].max())
)

map_df = df[df["year"] == map_year]

fig_map = px.choropleth(
    map_df,
    locations="country_code",          # ISO-3 REQUIRED
    color="electricity_use_kwh_per_capita",
    hover_name="country_name",          # HUMAN READABLE
    color_continuous_scale="YlOrRd",
    projection="natural earth",
    title=f"Electricity Use per Capita ({map_year})"
)

st.plotly_chart(fig_map, use_container_width=True)

# ---------------------------------------------------
# Top 5 Countries Bar Chart
# ---------------------------------------------------
st.subheader("Top 5 Countries by Electricity Use")

top5 = (
    map_df.sort_values("electricity_use_kwh_per_capita", ascending=False)
    .head(5)
)

fig_top5 = px.bar(
    top5,
    x="country_name",
    y="electricity_use_kwh_per_capita",
    text="electricity_use_kwh_per_capita",
    labels={"electricity_use_kwh_per_capita": "kWh per Capita"},
)

st.plotly_chart(fig_top5, use_container_width=True)

# ---------------------------------------------------
# Data Table
# ---------------------------------------------------
st.subheader(f"Data for {country}")

st.dataframe(
    filtered_df[
        [
            "country_name",
            "country_code",
            "year",
            "electricity_use_kwh_per_capita",
            "renewable_electricity_percent",
            "electricity_losses_pct"
        ]
    ]
)
