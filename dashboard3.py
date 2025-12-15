# ============================================================
# IMPORT LIBRARIES
# ============================================================
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import altair as alt


# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Global Electricity Analysis",
    layout="wide"
)

st.title("🌍 Global Electricity Analysis")
st.markdown(
    """
    This dashboard explores global electricity consumption, renewable electricity
    share, and transmission & distribution losses using World Bank datasets.
    """
)

# ============================================================
# LOAD DATA
# ============================================================
df = pd.read_csv("integrated_electricity_dataset.csv")

# ============================================================
# SIDEBAR FILTERS
# ============================================================
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

filtered_df = df[
    (df["country_name"] == country) &
    (df["year"] >= year_range[0]) &
    (df["year"] <= year_range[1])
]

# ============================================================
# KEY PERFORMANCE INDICATORS (KPIs)
# ============================================================
st.subheader("Key Performance Indicators (KPIs)")

if not filtered_df.empty:
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Mean Electricity Consumption (kWh per capita)",
        f"{filtered_df['electricity_use_kwh_per_capita'].mean():.0f}"
    )

    col2.metric(
        "Mean Renewable Electricity Share (%)",
        f"{filtered_df['renewable_electricity_percent'].mean():.1f}"
    )

    col3.metric(
        "Mean Transmission and Distribution Losses (%)",
        f"{filtered_df['electricity_losses_pct'].mean():.1f}"
    )

# ============================================================
# TIME-SERIES TREND ANALYSIS
# ============================================================
st.subheader("Electricity Consumption per Capita Over Time")
if not filtered_df.empty:
    st.line_chart(
        filtered_df.sort_values("year")
        .set_index("year")["electricity_use_kwh_per_capita"]
    )

st.subheader("Renewable Electricity Share Over Time")
if not filtered_df.empty:
    st.line_chart(
        filtered_df.sort_values("year")
        .set_index("year")["renewable_electricity_percent"]
    )

st.subheader("Transmission and Distribution Losses Over Time")
if not filtered_df.empty:
    st.line_chart(
        filtered_df.sort_values("year")
        .set_index("year")["electricity_losses_pct"]
    )

# ============================================================
# COMBINED AND COMPARATIVE VISUALISATIONS
# ============================================================
st.subheader("Dual-Axis Trend: Electricity Consumption vs Renewable Electricity")

if not filtered_df.empty:
    base = alt.Chart(filtered_df.sort_values("year")).encode(
        x=alt.X("year:O", title="Year")
    )

    line_use = base.mark_line(color="blue").encode(
        y=alt.Y("electricity_use_kwh_per_capita:Q",
                title="Electricity Use (kWh per capita)")
    )

    line_renew = base.mark_line(color="green").encode(
        y=alt.Y("renewable_electricity_percent:Q",
                title="Renewable Electricity Share (%)")
    )

    st.altair_chart(
        alt.layer(line_use, line_renew).resolve_scale(y="independent"),
        use_container_width=True
    )

# ============================================================
# INDEXED TREND CHART
# ============================================================
st.subheader("Indexed Comparison of Electricity Indicators (Base Year = 100)")

if not filtered_df.empty:
    idx_df = filtered_df.sort_values("year").copy()
    base_row = idx_df.iloc[0]

    idx_df["Electricity Use Index"] = (
        idx_df["electricity_use_kwh_per_capita"] /
        base_row["electricity_use_kwh_per_capita"] * 100
    )

    idx_df["Renewable Electricity Index"] = (
        idx_df["renewable_electricity_percent"] /
        base_row["renewable_electricity_percent"] * 100
    )

    idx_df["Losses Index"] = (
        idx_df["electricity_losses_pct"] /
        base_row["electricity_losses_pct"] * 100
    )

    idx_long = idx_df.melt(
        id_vars="year",
        value_vars=[
            "Electricity Use Index",
            "Renewable Electricity Index",
            "Losses Index"
        ],
        var_name="Indicator",
        value_name="Index Value"
    )

    st.altair_chart(
        alt.Chart(idx_long).mark_line().encode(
            x="year:O",
            y="Index Value:Q",
            color="Indicator:N"
        ),
        use_container_width=True
    )

# ============================================================
# CORRELATION ANALYSIS
# ============================================================
st.subheader("Scatter Plot: Electricity Use vs Transmission Losses")

if not filtered_df.empty:
    scatter = alt.Chart(filtered_df).mark_circle(size=90).encode(
        x="electricity_use_kwh_per_capita:Q",
        y="electricity_losses_pct:Q",
        color="year:Q",
        tooltip=[
            "country_name",
            "year",
            "electricity_use_kwh_per_capita",
            "electricity_losses_pct"
        ]
    )
    st.altair_chart(scatter, use_container_width=True)

# ============================================================
# RANKING AND COMPARATIVE ANALYSIS
# ============================================================
st.subheader("Top 5 Countries by Electricity Consumption")

map_year = st.slider(
    "Select Year for Ranking",
    int(df["year"].min()),
    int(df["year"].max()),
    int(df["year"].max())
)

top5_df = (
    df[df["year"] == map_year]
    .sort_values("electricity_use_kwh_per_capita", ascending=False)
    .head(5)
)

st.altair_chart(
    alt.Chart(top5_df).mark_bar().encode(
        x="electricity_use_kwh_per_capita:Q",
        y=alt.Y("country_name:N", sort="-x")
    ),
    use_container_width=True
)

# ============================================================
# BUMP CHART – RANK CHANGE OVER TIME
# ============================================================
st.subheader("Rank Change of Electricity Consumption Over Time (Bump Chart)")

rank_df = (
    df[df["country_name"].isin(top5_df["country_name"])]
    .sort_values(["year", "electricity_use_kwh_per_capita"],
                  ascending=[True, False])
)

rank_df["rank"] = rank_df.groupby("year")[
    "electricity_use_kwh_per_capita"
].rank(method="first", ascending=False)

bump_chart = alt.Chart(rank_df).mark_line(point=True).encode(
    x="year:O",
    y=alt.Y("rank:Q", scale=alt.Scale(reverse=True)),
    color="country_name:N",
    tooltip=["country_name", "year", "rank"]
)

st.altair_chart(bump_chart, use_container_width=True)

# ============================================================
# GEOGRAPHIC VISUALISATION
# ============================================================
st.subheader("Interactive World Map: Electricity Consumption per Capita")

world = gpd.read_file("world_countries.geojson")
geo_year_df = df[df["year"] == map_year]

geo_merged = world.merge(
    geo_year_df,
    left_on="id",
    right_on="country_code",
    how="left"
)

plotly_map = px.choropleth(
    geo_merged,
    geojson=geo_merged.geometry,
    locations=geo_merged.index,
    color="electricity_use_kwh_per_capita",
    color_continuous_scale="YlOrRd",
    hover_data={"country_name": True},
    title=f"Electricity Consumption per Capita ({map_year})"
)

plotly_map.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(plotly_map, use_container_width=True, key="map_main")

# ============================================================
# RESULTS & EVALUATION – KEY FIGURES
# ============================================================
st.markdown("---")
st.header("Results and Evaluation – Key Figures")

st.subheader("Electricity Consumption per Capita Over Time")
st.line_chart(
    filtered_df.sort_values("year")
    .set_index("year")["electricity_use_kwh_per_capita"]
)

st.subheader("Relationship Between Electricity Consumption and Transmission Losses")
st.altair_chart(scatter, use_container_width=True)

st.subheader("Global Distribution of Electricity Consumption per Capita")
st.plotly_chart(plotly_map, use_container_width=True, key="map_results")

# ============================================================
# DATA TABLE
# ============================================================
st.subheader(f"Detailed Data for {country}")
st.dataframe(filtered_df)
