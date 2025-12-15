# =========================
# IMPORTS
# =========================
import pandas as pd
import sqlite3
import requests
from pymongo import MongoClient
import pycountry


# =========================
# CONFIGURATION
# =========================
CSV_INPUT = "renewable_electricity.csv"
CSV_PROCESSED = "renewable_electricity_processed.csv"
CSV_LOSSES_PROCESSED = "electricity_losses_pct_xml_processed.csv"
CSV_FINAL = "integrated_electricity_dataset.csv"

SQLITE_DB = "electricity.db"

MONGO_URI = "mongodb+srv://taqApdvAdmin:T%40uq33r7861@electricitydatabase.rodgmrs.mongodb.net/?appName=electricityDatabase"
MONGO_DB = "electricity_db"
MONGO_COLLECTION = "electricity_use_per_capita"

JSON_URL = "https://api.worldbank.org/v2/country/all/indicator/EG.USE.ELEC.KH.PC?format=json&per_page=20000"
XML_URL = "https://api.worldbank.org/v2/country/all/indicator/EG.ELC.LOSS.ZS?per_page=20000"


# =========================
# HELPER FUNCTIONS
# =========================
def iso2_to_iso3(code):
    try:
        return pycountry.countries.get(alpha_2=code).alpha_3
    except:
        return None


def is_valid_iso3(code):
    try:
        return pycountry.countries.get(alpha_3=code) is not None
    except:
        return False


# =========================
# STEP 1: CSV → TRANSFORM → SQLITE
# =========================
def process_renewable_csv():
    print("\n[STEP 1] Loading renewable electricity CSV")
    df_raw = pd.read_csv(CSV_INPUT, skiprows=4)
    print("Raw shape:", df_raw.shape)

    year_cols = [c for c in df_raw.columns if c.isdigit()]
    print("Year columns:", year_cols[:5], "...", year_cols[-5:])

    print("\n[STEP 2] Melting wide → long format")
    df_transformed = df_raw.melt(
        id_vars=["Country Name", "Country Code"],
        value_vars=year_cols,
        var_name="year",
        value_name="renewable_electricity_percent"
    )
    print("After melt:", df_transformed.shape)

    print("\n[STEP 3] Cleaning data")
    df_transformed = df_transformed.dropna().copy()
    df_transformed["year"] = df_transformed["year"].astype(int)
    print("After dropna:", df_transformed.shape)
    print(df_transformed.info())

    print("\n[STEP 4] Writing processed CSV")
    df_transformed.to_csv(CSV_PROCESSED, index=False)
    print("CSV written:", CSV_PROCESSED)

    print("\n[STEP 5] Loading into SQLite")
    conn = sqlite3.connect(SQLITE_DB)
    df_transformed.to_sql(
        "renewable_electricity",
        conn,
        if_exists="replace",
        index=False
    )
    conn.close()
    print("SQLite table created: renewable_electricity")


# =========================
# STEP 2: JSON API → MONGODB
# =========================
def process_json_to_mongo():
    print("\n[STEP 6] Fetching JSON API data")
    response = requests.get(JSON_URL)
    json_data = response.json()

    records = []
    for item in json_data[1]:
        records.append({
            "country_name": item["country"]["value"],
            "country_code": item["country"]["id"],
            "year": item["date"],
            "electricity_use_kwh_per_capita": item["value"]
        })

    df_json = pd.DataFrame(records)
    print("Raw JSON DF:", df_json.shape)

    df_json = df_json.dropna().copy()
    df_json["year"] = df_json["year"].astype(int)
    print("Cleaned JSON DF:", df_json.shape)

    print("\n[STEP 7] Writing to MongoDB")
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION]

    collection.delete_many({})
    result = collection.insert_many(df_json.to_dict(orient="records"))
    print(f"Inserted {len(result.inserted_ids)} documents into MongoDB")


# =========================
# STEP 3: XML API → SQLITE
# =========================
def process_xml_to_sqlite():
    print("\n[STEP 8] Fetching XML API data")
    df_xml = pd.read_xml(XML_URL)

    
    df_xml = df_xml.rename(columns={
        "country": "country_name",
        "countryiso3code": "country_code",
        "date": "year",
        "value": "electricity_losses_pct"
    })


    df_xml = df_xml[[
        "country_name",
        "country_code",
        "year",
        "electricity_losses_pct"
    ]]

    print("Raw XML DF:", df_xml.shape)

    df_xml = df_xml.dropna().copy()
    df_xml["year"] = df_xml["year"].astype(int)
    df_xml["electricity_losses_pct"] = df_xml["electricity_losses_pct"].astype(float)
    print("Cleaned XML DF:", df_xml.shape)

    df_xml.to_csv(CSV_LOSSES_PROCESSED, index=False)
    print("CSV written:", CSV_LOSSES_PROCESSED)

    conn = sqlite3.connect(SQLITE_DB)
    df_xml.to_sql(
        "electricity_losses_pct",
        conn,
        if_exists="replace",
        index=False
    )
    conn.close()
    print("SQLite table created: electricity_losses_pct")


# =========================
# STEP 4: LOAD FROM DBS
# =========================
def load_from_databases():
    print("\n[STEP 9] Loading data from SQLite")
    conn = sqlite3.connect(SQLITE_DB)

    df_renewable = pd.read_sql("""
        SELECT
            "Country Name" AS country_name,
            "Country Code" AS country_code,
            year,
            renewable_electricity_percent
        FROM renewable_electricity
    """, conn)

    df_losses = pd.read_sql("""
        SELECT
            country_code,
            year,
            electricity_losses_pct
        FROM electricity_losses_pct
    """, conn)

    conn.close()
    print("Renewable:", df_renewable.shape)
    print("Losses:", df_losses.shape)

    print("\n[STEP 10] Loading data from MongoDB")
    client = MongoClient(MONGO_URI)
    collection = client[MONGO_DB][MONGO_COLLECTION]

    mongo_data = list(collection.find(
        {},
        {"_id": 0, "country_code": 1, "year": 1, "electricity_use_kwh_per_capita": 1}
    ))

    df_consumption = pd.DataFrame(mongo_data)
    print("Consumption:", df_consumption.shape)

    return df_renewable, df_losses, df_consumption


# =========================
# STEP 5: ISO NORMALIZATION
# =========================
def normalize_iso(df, name):
    print(f"\n[STEP] ISO normalization for {name}")
    df["iso3"] = df["country_code"].apply(
        lambda x: iso2_to_iso3(x) if len(x) == 2 else x
    )
    df = df[df["iso3"].apply(is_valid_iso3)]
    df = df.drop(columns=["country_code"])
    df = df.rename(columns={"iso3": "country_code"})
    print(f"{name} after ISO fix:", df.shape)
    return df


# =========================
# STEP 6: DATA INTEGRATION
# =========================
def integrate_and_store(df_renewable, df_losses, df_consumption):
    print("\n[STEP 11] Merging SQLite datasets")
    df_sqlite_merged = pd.merge(
        df_renewable,
        df_losses,
        on=["country_code", "year"],
        how="inner"
    )
    print("SQLite merged:", df_sqlite_merged.shape)

    print("\n[STEP 12] Merging with MongoDB dataset")
    df_final = pd.merge(
        df_sqlite_merged,
        df_consumption,
        on=["country_code", "year"],
        how="inner"
    )
    print("Final integrated:", df_final.shape)

    print("\n[STEP 13] Saving final outputs")
    df_final.to_csv(CSV_FINAL, index=False)

    conn = sqlite3.connect(SQLITE_DB)
    df_final.to_sql(
        "integrated_electricity_data",
        conn,
        if_exists="replace",
        index=False
    )
    conn.close()

    print("Final dataset saved (CSV + SQLite)")


# =========================
# MAIN PIPELINE
# =========================
def main():
    print("\n========== PIPELINE STARTED ==========")

    process_renewable_csv()
    process_json_to_mongo()
    process_xml_to_sqlite()

    df_renewable, df_losses, df_consumption = load_from_databases()

    df_renewable = normalize_iso(df_renewable, "Renewable")
    df_losses = normalize_iso(df_losses, "Losses")
    df_consumption = normalize_iso(df_consumption, "Consumption")

    integrate_and_store(df_renewable, df_losses, df_consumption)

    print("\n========== PIPELINE COMPLETED ==========")


if __name__ == "__main__":
    main()
