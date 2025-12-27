# 🌍 Global Electricity Analysis – APDV Project

This project presents an end-to-end analysis of global electricity systems using multiple datasets from the World Bank World Development Indicators (WDI). The work integrates heterogeneous data sources, automates data processing through a pipeline, and provides an interactive dashboard for exploratory analysis and visualisation.

The project is developed as part of the **Analytics Programming and Data Visualisation (APDV)** module.

---

## 📌 Project Objectives

- Integrate heterogeneous global electricity datasets from different formats (CSV, JSON, XML)
- Build an automated, reproducible data processing pipeline
- Store and manage structured and semi-structured data
- Perform exploratory data analysis and visualisation
- Provide an interactive dashboard for global electricity insights

---

## 📊 Datasets Used (World Bank Indicators)

The project uses three indicators from the **World Bank World Development Indicators (WDI)** database.

### 1️⃣ Electricity Use per Capita  
**Indicator Code:** EG.USE.ELEC.KH.PC  
**Description:** Average electricity consumption per person (kWh)

**JSON API URL:**  
https://api.worldbank.org/v2/country/all/indicator/EG.USE.ELEC.KH.PC?format=json&per_page=20000


### 2️⃣ Renewable Electricity Output (% of Total)  
**Indicator Code:** EG.ELC.RNEW.ZS  
**Description:** Percentage of electricity generated from renewable sources

**CSV Download URL:**  
https://api.worldbank.org/v2/en/indicator/EG.ELC.RNEW.ZS?downloadformat=csv


### 3️⃣ Electricity Transmission & Distribution Losses (%)  
**Indicator Code:** EG.ELC.LOSS.ZS  
**Description:** Percentage of electricity lost during transmission and distribution

**XML API URL:**  
https://api.worldbank.org/v2/country/all/indicator/EG.ELC.LOSS.ZS?per_page=20000


---

## 🗂️ Project Structure

#### apdvEnergyProject/

#### pipeline.py                  (Prefect-based automated data pipeline)
#### dashboard.py                 (Streamlit interactive dashboard)
#### integrated_electricity_dataset.csv (Final integrated dataset)
#### requirements.txt             (Python dependencies)
#### README.md                    (Project documentation)



---

## ⚙️ Technologies & Tools

- **Python** – core programming language  
- **Pandas & NumPy** – data processing and transformation  
- **Requests** – API data retrieval  
- **Prefect** – workflow orchestration and pipeline automation  
- **SQLite** – relational storage for structured data  
- **MongoDB** – NoSQL storage for semi-structured JSON data  
- **Streamlit** – interactive dashboard development  
- **Altair & Plotly** – data visualisation  
- **GeoPandas** – geographic visualisation  

---

## 🗄️ Database Connections

- **SQLite:** Accessed locally using Python’s `sqlite3` library by directly opening the database file (no server-based connection required).
- **MongoDB:** Connected using a MongoDB connection string via the `pymongo` client to communicate with the MongoDB server - mongodb+srv://taqApdvAdmin:T%40uq33r7861@electricitydatabase.rodgmrs.mongodb.net/?appName=electricityDatabase.


## 🔄 Data Processing Pipeline

The automated pipeline performs the following steps:

1. Load renewable electricity data from CSV
2. Fetch electricity consumption data via JSON API
3. Fetch electricity transmission & distribution losses via XML API
4. Clean and standardise all datasets
5. Harmonise country identifiers using ISO-3 codes
6. Integrate datasets using `country_code` and `year`
7. Store intermediate and final datasets
8. Generate a unified dataset for dashboard visualisation

The pipeline is implemented using **Prefect**, ensuring reproducibility and modular task execution.

---
## 🌐 Deployed Dashboard URL 
    https://apdvenergyproject-jaokeqwr3txvnbxc8r8suc.streamlit.app/
---
## 💻 Github Source Code Github Repository URL
    https://github.com/tauqeerqau/apdvEnergyProject
---
## 📈 Interactive Dashboard

The Streamlit dashboard enables users to:

- Filter data by **country** and **year range**
- View **Key Performance Indicators (KPIs)**
- Analyse **time-series trends**
- Compare **renewable electricity adoption**
- Explore **correlations between consumption and losses**
- View **country rankings and rank changes**
- Visualise **global electricity consumption using an interactive world map**

---

## 🚀 How to Run the Project

### 1️⃣ Install Dependencies
pip install -r requirements.txt

### 2️⃣ Please keep file in your folder
world_countries.geojson

### 3️⃣ Run the Data Pipeline
python pipeline.py

### 4️⃣ Run the Dashboard
streamlit run dashboard.py

### 👥 Team Members & Contributions

#### Tauqeer ul Hassan
CSV dataset processing, data integration, pipeline development, dashboard design

#### Eisa Bin Ahsan
JSON dataset processing, API handling, MongoDB storage

#### Zain Bin Yaseen
XML dataset processing, data parsing, integration support
