# ============================================
# Global Electricity Data Pipeline (Prefect)
# ============================================

from prefect import flow, task
import pandas as pd
import sqlite3
import requests
import pycountry


# --------------------------------------------
# Utility: Convert ISO-2 to ISO-3
# --------------------------------------------
def iso2_to_iso3(code):
    try:
        return pycountry.countries.get(alpha_2=code).alpha_3
    except:
        return None


# --------------------------------------------
# Task 1: Fetch Electricity Consumption (JSON)
# Indicator: EG.USE.ELEC.KH.PC
# --------------------------------------------
@task
def fetch_consumption_data():
    url = (
        "https://api.worldbank.org/v2/country/all/"
        "indicator/EG.USE.ELEC.KH.PC?format=json&per_page=20000"
    )

    response = requests.get(url)
    data = response.json()[1]

    rows = []

    for item in data:
        iso3 = iso2_to_iso3(item["country"]["id"])

        if iso3 and item["value"] is not None:
            rows.append({
                "country_code": iso3,
                "year": int(item["date"]),
                "electricity_use_kwh_per_capita": item["value"]
            })

    df = pd.DataFrame(rows)
    return df


# --------------------------------------------
# Task 2: Load Renewable Electricity (CSV)
# Indicator: EG.ELC.RNEW.ZS
# --------------------------------------------
@task
def load_renewable_data():
    df = pd.read_csv("renewable_electricity_processed.csv")

    # IMPORTANT: Standardize column names
    df = df.rename(columns={
        "Country Code": "country_code",
        "Country Name": "country_name"
    })

    return df


# --------------------------------------------
# Task 3: Load Electricity Losses (SQLite)
# Indicator: EG.ELC.LOSS.ZS
# --------------------------------------------
@task
def load_losses_data():
    conn = sqlite3.connect("electricity.db")

    df = pd.read_sql(
        "SELECT * FROM electricity_losses_pct",
        conn
    )

    conn.close()
    return df


# --------------------------------------------
# Task 4: Integrate All Datasets
# Join Keys: country_code + year
# --------------------------------------------
@task
def integrate_data(consumption, renewable, losses):

    # Merge renewable + losses
    df = renewable.merge(
        losses,
        on=["country_code", "year"],
        how="inner"
    )

    # Merge with consumption
    df = df.merge(
        consumption,
        on=["country_code", "year"],
        how="inner"
    )

    return df


# --------------------------------------------
# Task 5: Save Final Integrated Dataset
# --------------------------------------------
@task
def save_final_dataset(df):
    df.to_csv(
        "integrated_electricity_dataset.csv",
        index=False
    )


# --------------------------------------------
# Prefect Flow Definition
# --------------------------------------------
@flow(name="Global Electricity Data Pipeline")
def electricity_pipeline():

    consumption = fetch_consumption_data()
    renewable = load_renewable_data()
    losses = load_losses_data()

    integrated = integrate_data(
        consumption,
        renewable,
        losses
    )

    save_final_dataset(integrated)


# --------------------------------------------
# Run Pipeline
# --------------------------------------------
if __name__ == "__main__":
    electricity_pipeline()
