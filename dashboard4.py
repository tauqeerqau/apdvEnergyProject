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
        "Mean Transmission & Distribution Losses (%)",
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
# COMBINED TREND (DUAL AXIS)
# ============================================================
st.subheader("Electricity Consumption vs Renewable Electricity (Dual-Axis Trend)")

if not filtered_df.empty:
    base = alt.Chart(filtered_df.sort_values("year")).encode(
        x=alt.X("year:O", title="Year")
    )

    line_use = base.mark_line(color="steelblue").encode(
        y=alt.Y(
            "electricity_use_kwh_per_capita:Q",
            title="Electricity Use (kWh per capita)"
        )
    )

    line_renew = base.mark_line(color="green").encode(
        y=alt.Y(
            "renewable_electricity_percent:Q",
            title="Renewable Electricity Share (%)"
        )
    )

    st.altair_chart(
        alt.layer(line_use, line_renew).resolve_scale(y="independent"),
        width="stretch"
    )

# ============================================================
# INDEXED COMPARISON (BASE YEAR = 100)
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
        width="stretch"
    )

# ============================================================
# CORRELATION ANALYSIS
# ============================================================
st.subheader("Electricity Use vs Transmission Losses")

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

    st.altair_chart(scatter, width="stretch")

# ============================================================
# TOP COUNTRIES & BUMP CHART
# ============================================================
st.subheader("Top 10 Countries by Electricity Consumption")

map_year = st.slider(
    "Select Year for Ranking & Maps",
    int(df["year"].min()),
    int(df["year"].max()),
    int(df["year"].max())
)

top5_df = (
    df[df["year"] == map_year]
    .sort_values("electricity_use_kwh_per_capita", ascending=False)
    .head(10)
)

st.altair_chart(
    alt.Chart(top5_df).mark_bar().encode(
        x="electricity_use_kwh_per_capita:Q",
        y=alt.Y("country_name:N", sort="-x")
    ),
    width="stretch"
)

st.subheader("Rank Change of Electricity Consumption Over Time")

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

st.altair_chart(bump_chart, width="stretch")

# ============================================================
# GEOGRAPHIC VISUALISATIONS
# ============================================================
world = gpd.read_file("world_countries.geojson")
geo_year_df = df[df["year"] == map_year]

geo_merged = world.merge(
    geo_year_df,
    left_on="id",
    right_on="country_code",
    how="left"
)

st.subheader("World Map: Electricity Consumption per Capita")

consumption_map = px.choropleth(
    geo_merged,
    geojson=geo_merged.geometry,
    locations=geo_merged.index,
    color="electricity_use_kwh_per_capita",
    color_continuous_scale="YlOrRd",
    hover_data={"country_name": True},
    title=f"Electricity Consumption per Capita ({map_year})"
)

consumption_map.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(consumption_map, width="stretch", key="map_consumption")

st.subheader("World Map: Renewable Electricity Share (%)")

renewable_map = px.choropleth(
    geo_merged,
    geojson=geo_merged.geometry,
    locations=geo_merged.index,
    color="renewable_electricity_percent",
    color_continuous_scale="Greens",
    hover_data={
        "country_name": True,
        "renewable_electricity_percent": ":.1f"
    },
    title=f"Renewable Electricity Share (%) ({map_year})"
)

renewable_map.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(renewable_map, width="stretch", key="map_renewable")

# ============================================================
# DATA TABLE
# ============================================================
st.subheader(f"Detailed Data for {country}")
st.dataframe(filtered_df)
