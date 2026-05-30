# AireBA Trends

Historical Air Quality Trends and Anomaly Detection for Buenos Aires

## Project Summary

AireBA Trends is a static open data project built for the Building AI course. It analyzes official air quality records from the City of Buenos Aires between 2009 and 2026 and focuses on three pollutants:

- NO2
- CO
- PM10

The project transforms raw official datasets into reproducible CSV and JSON outputs, then presents the results in a lightweight dashboard that can be deployed with GitHub Pages.

This is a historical and exploratory project. It is not a real-time alert system, it does not forecast future pollution, and it does not prove the causes of unusual events.

## What the Project Does

The pipeline:

- loads raw official datasets from `data/raw/`
- cleans and normalizes mixed CSV and Excel sources
- resolves overlapping source files and duplicate observations
- transforms air quality data from wide format to long format
- aggregates hourly measurements into daily values
- calculates yearly and monthly pollutant trends
- detects unusual daily events
- exports processed CSV files to `data/processed/`
- exports frontend-ready JSON files to `docs/data/`

The dashboard:

- shows summary cards
- lets users filter by pollutant, station, year, and anomaly severity
- displays yearly pollutant trends
- displays monthly seasonality as a heatmap
- shows an anomaly ranking table
- shows anomaly charts
- shows official monitoring stations on a map

## Why This Project Matters

Air quality data is publicly available, but raw environmental datasets are usually difficult to explore directly. Long-term trends, seasonal behavior, and unusual pollution spikes are not easy to understand from raw tables alone.

AireBA Trends aims to make that data easier to explore for:

- students
- citizens
- journalists
- researchers
- open data enthusiasts

## Data Source

Data source: official open data from the Government of Buenos Aires City.

The repository currently uses these raw files:

- `calidad-aire.csv`
- `calidad-de-aire-2017.xlsx`
- `calidad-de-aire-2018.xlsx`
- `calidad-de-aire-2019.xlsx`
- `calidad_aire_2025.csv`
- `calidad_aire_2026.csv`
- `estaciones-ambientales.xlsx`
- `contaminantes.xlsx`

## Repository Structure

```text
aireba-trends/
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── data/
├── notebooks/
│   └── exploration.ipynb
├── scripts/
│   ├── main.py
│   ├── load_data.py
│   ├── clean_data.py
│   ├── transform_data.py
│   ├── trend_analysis.py
│   ├── anomaly_detection.py
│   └── export_static_data.py
├── AGENTS.md
├── LICENSE
├── pyproject.toml
├── README.md
└── uv.lock
```

## How to Run the Pipeline

This project uses `uv` as the Python dependency manager.

### 1. Install dependencies

```bash
uv sync
```

### 2. Run the full pipeline

```bash
uv run python scripts/main.py
```

This command:

1. loads the raw datasets
2. cleans and normalizes them
3. consolidates overlapping source files
4. transforms the data into long format
5. generates daily, yearly, and monthly outputs
6. detects anomalies
7. exports CSV files to `data/processed/`
8. exports JSON files to `docs/data/`

## How to View the Dashboard

Serve the `docs/` directory locally:

```bash
uv run python -m http.server 8000 -d docs
```

Then open:

```text
http://localhost:8000
```

The static site is designed to be compatible with GitHub Pages.

## Output Files

### Processed CSV files

Generated in `data/processed/`:

- `air_quality_long.csv`
- `daily_air_quality.csv`
- `yearly_trends.csv`
- `monthly_trends.csv`
- `anomalies.csv`
- `station_summary.csv`
- `pollutant_summary.csv`
- `source_overlap_report.csv`

### Frontend JSON files

Generated in `docs/data/`:

- `summary.json`
- `yearly_trends.json`
- `monthly_trends.json`
- `anomalies.json`
- `stations.json`
- `metadata.json`

## Data Model

### Long air quality table

Main fields:

- `datetime`
- `date`
- `year`
- `month`
- `day`
- `hour`
- `station`
- `pollutant`
- `value`
- `latitude`
- `longitude`
- `zone`

### Daily table

Main fields:

- `date`
- `year`
- `month`
- `station`
- `pollutant`
- `daily_avg`
- `daily_min`
- `daily_max`
- `daily_median`
- `daily_std`
- `records_count`

## Methods

### Trend analysis

The pipeline computes yearly and monthly summaries by:

- station
- pollutant

Main statistics:

- mean
- median
- minimum
- maximum
- standard deviation
- record count

### Anomaly detection

The project uses daily aggregated data to detect unusual pollution events.

Implemented methods:

- IQR baseline by `station + pollutant`
- Isolation Forest by `station + pollutant` when enough historical data exists

Isolation Forest features currently include:

- `daily_avg`
- `month`
- `year`
- `day_of_week`
- `rolling_mean_7d`
- `rolling_mean_30d`
- `rolling_std_30d`

Important note:

- anomaly rates are measured against the daily aggregated table, not the hourly long table

Detected anomalies indicate unusual values. They do not prove the cause of the event.

## Frontend Behavior

The frontend is intentionally static:

- no backend
- no client-side model training
- no live data fetching from official sources
- no recalculation of trends or anomalies in the browser

All heavy processing happens in Python before export.

## Current Scope

Included:

- historical trend analysis
- monthly and yearly summaries
- source overlap consolidation
- station-level comparison
- pollutant-level comparison
- daily anomaly detection
- static CSV and JSON exports
- static dashboard

Not included:

- real-time alerts
- forecasting
- street-level pollution estimation
- causal attribution
- medical guidance
- public policy recommendations
- backend API
- user authentication

## Limitations

- The project is historical and exploratory.
- The project is not a real-time alert system.
- The project does not predict future pollution.
- The project does not prove causes of pollution peaks.
- The project depends on official dataset quality.
- The project only represents areas covered by official monitoring stations.
- Some stations have incomplete or irregular historical coverage.
- The project should not replace official environmental reports.

## Ethical Considerations

- Unusual events are presented as anomalies, not confirmed causes.
- The dashboard should not be interpreted as a public safety alert system.
- Missing values, station shutdowns, and inconsistent source coverage can affect the analysis.
- Results should be read as an exploratory data product, not as regulatory or medical advice.

## Libraries and Tools Used

- Python
- pandas
- NumPy
- scikit-learn
- openpyxl
- Plotly.js
- Leaflet.js
- GitHub Pages
- uv

## Course Context

This project was created as a final project for the Building AI course by Reaktor and the University of Helsinki.

The AI component is anomaly detection. Instead of building a predictive system, the project uses interpretable statistical baselines and an unsupervised anomaly detection model to highlight daily values that behave differently from the historical pattern of the same station and pollutant.
