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
    Multiple visualisations are included for exploratory analysis.
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
    "Select Country (ISO-3)",
    sorted(df["country_code"].unique())
)

year_range = st.sidebar.slider(
    "Select Year Range",
    int(df["year"].min()),
    int(df["year"].max()),
    (
        int(df["year"].min()),
        int(df["year"].max())
    )
)

filtered_df = df[
    (df["country_code"] == country) &
    (df["year"] >= year_range[0]) &
    (df["year"] <= year_range[1])
]


# ============================================================
# KPI METRICS
# ============================================================
st.subheader("📌 Key Indicators (Selected Filters)")

if not filtered_df.empty:
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Avg Electricity Use (kWh/capita)",
        f"{filtered_df['electricity_use_kwh_per_capita'].mean():.0f}"
    )

    col2.metric(
        "Avg Renewable Electricity (%)",
        f"{filtered_df['renewable_electricity_percent'].mean():.1f}"
    )

    col3.metric(
        "Avg Electricity Losses (%)",
        f"{filtered_df['electricity_losses_pct'].mean():.1f}"
    )
else:
    st.warning("No data available for selected filters.")


# ============================================================
# GEO PANDAS MAP (STATIC)
# ============================================================
st.subheader("🗺️ GeoPandas Map – Electricity Use per Capita")

map_year = st.slider(
    "Select Year for Maps",
    int(df["year"].min()),
    int(df["year"].max()),
    int(df["year"].max())
)

world = gpd.read_file("world_countries.geojson")

geo_year_df = df[df["year"] == map_year]

geo_merged = world.merge(
    geo_year_df,
    left_on="id",
    right_on="country_code",
    how="left"
)

fig = geo_merged.plot(
    column="electricity_use_kwh_per_capita",
    cmap="OrRd",
    legend=True,
    figsize=(14, 6),
    missing_kwds={"color": "lightgrey"}
).figure

st.pyplot(fig)


# ============================================================
# PLOTLY INTERACTIVE WORLD MAP
# ============================================================
st.subheader("🌍 Interactive World Map (Plotly)")

plotly_map = px.choropleth(
    geo_merged,
    geojson=geo_merged.geometry,
    locations=geo_merged.index,
    color="electricity_use_kwh_per_capita",
    color_continuous_scale="YlOrRd",
    labels={"electricity_use_kwh_per_capita": "kWh per capita"},
    title=f"Electricity Use per Capita ({map_year})"
)

plotly_map.update_geos(fitbounds="locations", visible=False)
st.plotly_chart(plotly_map, use_container_width=True)


# ============================================================
# TOP 5 COUNTRIES BY ELECTRICITY USE
# ============================================================
st.subheader("🏅 Top 5 Countries by Electricity Use")

top5_df = (
    df[df["year"] == map_year]
    .sort_values("electricity_use_kwh_per_capita", ascending=False)
    .head(5)
)

st.altair_chart(
    alt.Chart(top5_df)
    .mark_bar()
    .encode(
        x="electricity_use_kwh_per_capita:Q",
        y=alt.Y("country_code:N", sort="-x"),
        tooltip=["country_code", "electricity_use_kwh_per_capita"]
    ),
    use_container_width=True
)


# ============================================================
# COMBINED TREND: USE VS RENEWABLE
# ============================================================
st.subheader("📈 Electricity Use vs Renewable Electricity (Combined Trend)")

if not filtered_df.empty:
    chart_data = filtered_df.sort_values("year")

    base = alt.Chart(chart_data).encode(
        x=alt.X("year:O", title="Year")
    )

    line_use = base.mark_line(color="blue").encode(
        y=alt.Y("electricity_use_kwh_per_capita:Q", title="Electricity Use (kWh/capita)")
    )

    line_renew = base.mark_line(color="green").encode(
        y=alt.Y("renewable_electricity_percent:Q", title="Renewable Electricity (%)")
    )

    st.altair_chart(
        alt.layer(line_use, line_renew).resolve_scale(y="independent"),
        use_container_width=True
    )


# ============================================================
# AREA CHART – RENEWABLE SHARE
# ============================================================
st.subheader("🌱 Renewable Electricity Share (Area Chart)")

if not filtered_df.empty:
    area_chart = alt.Chart(filtered_df.sort_values("year")).mark_area(
        opacity=0.6,
        color="green"
    ).encode(
        x="year:O",
        y="renewable_electricity_percent:Q",
        tooltip=["year", "renewable_electricity_percent"]
    )

    st.altair_chart(area_chart, use_container_width=True)


# ============================================================
# SCATTER: LOSSES VS CONSUMPTION
# ============================================================
st.subheader("🔗 Electricity Losses vs Consumption")

if not filtered_df.empty:
    scatter = alt.Chart(filtered_df).mark_circle(size=90).encode(
        x="electricity_use_kwh_per_capita:Q",
        y="electricity_losses_pct:Q",
        color="year:Q",
        tooltip=[
            "year",
            "electricity_use_kwh_per_capita",
            "electricity_losses_pct"
        ]
    )

    st.altair_chart(scatter, use_container_width=True)


# ============================================================
# BUBBLE CHART (3 VARIABLES)
# ============================================================
st.subheader("🟢 Bubble Chart (Use vs Losses, Size = Renewable %)")

if not filtered_df.empty:
    bubble = alt.Chart(filtered_df).mark_circle(opacity=0.7).encode(
        x="electricity_use_kwh_per_capita:Q",
        y="electricity_losses_pct:Q",
        size=alt.Size(
            "renewable_electricity_percent:Q",
            scale=alt.Scale(range=[100, 2000])
        ),
        color="year:Q",
        tooltip=[
            "year",
            "electricity_use_kwh_per_capita",
            "electricity_losses_pct",
            "renewable_electricity_percent"
        ]
    )

    st.altair_chart(bubble, use_container_width=True)


# ============================================================
# HEATMAP – ELECTRICITY USE INTENSITY
# ============================================================
st.subheader("🔥 Heatmap – Electricity Use Intensity (Top 5 Countries)")

heat_df = df[df["country_code"].isin(top5_df["country_code"])]

heatmap = alt.Chart(heat_df).mark_rect().encode(
    x="year:O",
    y="country_code:N",
    color="electricity_use_kwh_per_capita:Q",
    tooltip=["country_code", "year", "electricity_use_kwh_per_capita"]
)

st.altair_chart(heatmap, use_container_width=True)


# ============================================================
# INDEXED COMPARISON (BASE YEAR = 100)
# ============================================================
st.subheader("📊 Indexed Comparison of Indicators")

if not filtered_df.empty:
    idx_df = filtered_df.sort_values("year").copy()
    base_row = idx_df.iloc[0]

    idx_df["Use Index"] = idx_df["electricity_use_kwh_per_capita"] / base_row["electricity_use_kwh_per_capita"] * 100
    idx_df["Renewable Index"] = idx_df["renewable_electricity_percent"] / base_row["renewable_electricity_percent"] * 100
    idx_df["Losses Index"] = idx_df["electricity_losses_pct"] / base_row["electricity_losses_pct"] * 100

    idx_long = idx_df.melt(
        id_vars="year",
        value_vars=["Use Index", "Renewable Index", "Losses Index"],
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
# SIMPLE COMBINED LINE CHART
# ============================================================
st.subheader("📉 Simple Combined Time-Series")

if not filtered_df.empty:
    st.line_chart(
        filtered_df.sort_values("year")
        .set_index("year")[
            [
                "electricity_use_kwh_per_capita",
                "renewable_electricity_percent",
                "electricity_losses_pct"
            ]
        ]
    )


# ============================================================
# SINGLE INDIVIDUAL CHARTS (ALL THREE)
# ============================================================
st.subheader("📉 Electricity Use per Capita (Single Chart)")
if not filtered_df.empty:
    st.line_chart(
        filtered_df.sort_values("year")
        .set_index("year")["electricity_use_kwh_per_capita"]
    )

st.subheader("🌱 Renewable Electricity (%) (Single Chart)")
if not filtered_df.empty:
    st.line_chart(
        filtered_df.sort_values("year")
        .set_index("year")["renewable_electricity_percent"]
    )

st.subheader("⚡ Electricity Losses (%) (Single Chart)")
if not filtered_df.empty:
    st.line_chart(
        filtered_df.sort_values("year")
        .set_index("year")["electricity_losses_pct"]
    )


# ============================================================
# DATA TABLE
# ============================================================
st.subheader(f"📄 Detailed Data for {country}")
st.dataframe(filtered_df)
