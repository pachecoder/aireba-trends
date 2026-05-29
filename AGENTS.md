# AGENTS.md

## Project: AireBA Trends

AireBA Trends is an open source static data project for the Building AI course. It analyzes official air quality data from Buenos Aires City between 2009 and 2026, focused on three pollutants: NO2, CO and PM10.

The project must generate static datasets, charts, and a lightweight frontend dashboard that can be deployed with GitHub Pages.

The project is not a real-time alert system, does not forecast future pollution, and does not claim causality for pollution events.

---

## Main Goal

Build a reproducible data pipeline and static dashboard that:

1. Loads official Buenos Aires air quality datasets.
2. Cleans and normalizes the data.
3. Transforms the dataset from wide format to long format.
4. Analyzes historical trends by year and month.
5. Compares pollutants by monitoring station.
6. Detects unusual daily pollution events.
7. Exports static JSON and CSV files.
8. Displays the results in a static GitHub Pages dashboard.

---

## Scope

### Included

- Historical data analysis.
- Trend analysis by year.
- Trend analysis by month.
- Analysis by monitoring station.
- Analysis by pollutant.
- Detection of unusual daily values.
- Static JSON and CSV generation.
- Static frontend dashboard.
- Summary cards.
- Charts.
- Anomaly tables.
- Basic station map.

### Not included

- Real-time alerts.
- Live data ingestion.
- Future forecasting.
- Street-level pollution prediction.
- Causal explanation of anomalies.
- Medical recommendations.
- Government-level policy recommendations.
- Backend API.
- Database.
- User authentication.
- Deep learning.

---

## Pollutants

The first version must focus only on:

- NO2
- CO
- PM10

Do not add other pollutants unless the data pipeline is explicitly extended and documented.

---

## Expected Repository Structure

```text
aireba-trends/
├── data/
│   ├── raw/
│   │   ├── air_quality.csv
│   │   ├── stations.csv
│   │   └── pollutants.csv
│   │
│   └── processed/
│       ├── air_quality_long.csv
│       ├── daily_air_quality.csv
│       ├── yearly_trends.csv
│       ├── monthly_trends.csv
│       ├── anomalies.csv
│       ├── station_summary.csv
│       └── pollutant_summary.csv
│
├── docs/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── data/
│       ├── summary.json
│       ├── yearly_trends.json
│       ├── monthly_trends.json
│       ├── anomalies.json
│       ├── stations.json
│       └── metadata.json
│
├── notebooks/
│   └── exploration.ipynb
│
├── scripts/
│   ├── main.py
│   ├── load_data.py
│   ├── clean_data.py
│   ├── transform_data.py
│   ├── trend_analysis.py
│   ├── anomaly_detection.py
│   ├── export_static_data.py
│   └── generate_charts.py
│
├── README.md
├── AGENTS.md
├── requirements.txt
└── LICENSE
```

---

## Data Pipeline Responsibilities

The Python pipeline must be responsible for all heavy processing.

The frontend must not calculate trends, anomalies, or machine learning results.

### Pipeline steps

1. Read raw official datasets.
2. Standardize column names.
3. Parse date and hour fields.
4. Filter pollutants to NO2, CO and PM10.
5. Transform air quality measurements from wide format to long format.
6. Merge measurements with station metadata.
7. Aggregate hourly records into daily values if needed.
8. Calculate yearly trends.
9. Calculate monthly trends.
10. Detect daily anomalies.
11. Export processed CSV files to `data/processed`.
12. Export frontend-ready JSON files to `docs/data`.

---

## Input Data

### Air quality measurements

Expected raw format may include columns like:

```text
fecha
hora
co_centenario
no2_centenario
pm10_centenario
co_cordoba
no2_cordoba
pm10_cordoba
co_la_boca
no2_la_boca
pm10_la_boca
```

### Stations dataset

Expected fields:

```text
station
latitude
longitude
address
zone
pollutants
```

Actual raw names can differ. The pipeline should normalize them.

### Pollutants dataset

Expected fields:

```text
pollutant
description
unit
```

---

## Core Data Model

### Long air quality table

The normalized long table must contain:

```text
datetime
date
year
month
day
hour
station
pollutant
value
latitude
longitude
zone
```

### Daily table

The daily aggregation table should contain:

```text
date
year
month
station
pollutant
daily_avg
daily_min
daily_max
daily_median
daily_std
records_count
```

### Yearly trends table

```text
year
station
pollutant
avg_value
median_value
max_value
min_value
std_value
records_count
```

### Monthly trends table

```text
year
month
station
pollutant
avg_value
median_value
max_value
min_value
std_value
records_count
```

### Anomalies table

```text
date
station
pollutant
actual_value
expected_value
difference
percentage_difference
z_score
method
severity
is_anomaly
```

---

## Trend Analysis Requirements

Generate yearly and monthly summaries for each:

```text
station + pollutant
```

The project must support answering:

- How did NO2 evolve over the years by station?
- How did CO evolve over the years by station?
- How did PM10 evolve over the years by station?
- Are there monthly or seasonal patterns?
- Which station had higher average values?
- Which pollutant showed more variability?

Recommended calculations:

- mean
- median
- minimum
- maximum
- standard deviation
- record count

---

## Anomaly Detection Requirements

The project must detect unusual daily pollution events by comparing each daily value against the historical behavior of the same station and pollutant.

Anomalies are unusual values, not proven causes.

### Baseline methods

Implement at least one simple statistical method:

- Z-score
- IQR
- rolling mean plus standard deviation

Recommended first version:

- Use daily values.
- Group by `station + pollutant`.
- Calculate historical median and IQR.
- Mark values above `Q3 + 1.5 * IQR` as possible anomalies.
- Mark values above `Q3 + 3 * IQR` as extreme anomalies.

### Optional machine learning method

Add Isolation Forest as the simple AI/ML component.

Isolation Forest should be used as unsupervised anomaly detection. The dataset does not contain labels saying which days are anomalies.

Recommended features for Isolation Forest:

```text
daily_avg
month
year
day_of_week
rolling_mean_7d
rolling_mean_30d
rolling_std_30d
```

Run the model separately per `station + pollutant` where enough data exists.

### Severity levels

Use simple severity labels:

```text
Normal
Moderate
High
Extreme
```

Suggested rules:

```text
z_score < 2       => Normal
z_score 2 to 3    => Moderate
z_score 3 to 4    => High
z_score > 4       => Extreme
```

Or with IQR:

```text
inside expected range        => Normal
above Q3 + 1.5 * IQR         => Moderate
above Q3 + 3.0 * IQR         => Extreme
```

---

## Static Exports

The pipeline must export frontend-ready JSON files into:

```text
docs/data/
```

Required files:

```text
summary.json
yearly_trends.json
monthly_trends.json
anomalies.json
stations.json
metadata.json
```

### summary.json

Example:

```json
{
  "project_name": "AireBA Trends",
  "period_start": 2009,
  "period_end": 2026,
  "latest_available_date": "2026-05-21",
  "pollutants": ["NO2", "CO", "PM10"],
  "stations_count": 4,
  "total_records": 123456,
  "anomalies_detected": 350
}
```

### yearly_trends.json

Example:

```json
[
  {
    "year": 2020,
    "station": "Centenario",
    "pollutant": "NO2",
    "avg_value": 24.5,
    "median_value": 22.1,
    "max_value": 80.3,
    "min_value": 5.2,
    "std_value": 10.4,
    "records_count": 8700
  }
]
```

### monthly_trends.json

Example:

```json
[
  {
    "year": 2020,
    "month": 8,
    "station": "La Boca",
    "pollutant": "PM10",
    "avg_value": 37.2,
    "median_value": 35.8,
    "max_value": 95.0,
    "min_value": 12.4,
    "std_value": 14.2,
    "records_count": 720
  }
]
```

### anomalies.json

Example:

```json
[
  {
    "date": "2022-08-15",
    "station": "La Boca",
    "pollutant": "PM10",
    "actual_value": 95.0,
    "expected_value": 35.0,
    "difference": 60.0,
    "percentage_difference": 171.4,
    "z_score": 4.7,
    "method": "IQR + Isolation Forest",
    "severity": "Extreme"
  }
]
```

### stations.json

Example:

```json
[
  {
    "station": "Centenario",
    "latitude": -34.606,
    "longitude": -58.435,
    "address": "Parque Centenario",
    "zone": "Urban park",
    "pollutants": ["CO", "NO2", "PM10"]
  }
]
```

---

## Frontend Responsibilities

The frontend must live in:

```text
docs/
```

It must work on GitHub Pages without backend or build step.

Preferred technologies:

- HTML
- CSS
- JavaScript vanilla
- Plotly.js
- Leaflet.js if a map is included

Avoid frameworks unless explicitly requested.

### Frontend must show

1. Hero section.
2. Project description.
3. Summary cards.
4. Global filters.
5. Yearly trend chart.
6. Monthly trend chart or heatmap.
7. Anomalies ranking table.
8. Anomalies chart.
9. Stations map or station table.
10. Methodology note.
11. Data source and acknowledgments.

### Frontend must not

- Train models.
- Calculate anomalies.
- Clean raw data.
- Recalculate trends.
- Fetch live official datasets.
- Require backend services.

---

## Frontend Sections

### Hero

Title:

```text
AireBA Trends
```

Subtitle:

```text
Historical Air Quality Trends and Anomaly Detection for Buenos Aires
```

Description:

```text
A static open data dashboard that analyzes official Buenos Aires air quality records from 2009 to 2026, focused on NO2, CO and PM10.
```

### Summary cards

Read from `summary.json`.

Show:

- Period analyzed.
- Latest available date.
- Pollutants analyzed.
- Stations analyzed.
- Total records.
- Anomalies detected.

### Filters

Implement simple filters:

- Station.
- Pollutant.
- Year.
- Severity.

Filters should affect charts and tables when applicable.

### Yearly trends chart

Use `yearly_trends.json`.

Recommended chart:

```text
X axis: year
Y axis: avg_value
Group: station
Filter: pollutant
```

### Monthly trends chart

Use `monthly_trends.json`.

Recommended visualization:

- Heatmap year/month for selected station and pollutant.

Alternative:

- Line chart by month.

### Anomalies ranking table

Use `anomalies.json`.

Columns:

- Date.
- Station.
- Pollutant.
- Actual value.
- Expected value.
- Difference percent.
- Z-score.
- Severity.
- Method.

Show top 20 or top 50 by default.

Allow sorting by:

- percentage_difference.
- z_score.
- severity.
- date.

### Anomalies chart

Recommended chart:

```text
Number of anomalies by year and pollutant
```

Alternative chart:

```text
Top 20 anomalies by percentage difference
```

### Stations map

Use `stations.json`.

If Leaflet.js is used, each marker should show:

- Station name.
- Address.
- Zone.
- Pollutants measured.

Do not interpolate values or create estimated pollution zones.

---

## Methodology Note

The dashboard must include this kind of explanation:

```text
Anomalies are detected by comparing each daily pollutant value against the historical behavior of the same station and pollutant. The project uses statistical baselines such as IQR or Z-score and may include an unsupervised machine learning model such as Isolation Forest. Detected anomalies indicate unusual values, but they do not prove the cause of the event.
```

---

## Data Source Note

The dashboard and README must mention:

```text
Data source: official open data from the Government of Buenos Aires City.
```

Also mention the libraries used.

---

## Coding Style

### Python

- Use clear function names.
- Keep each script focused.
- Avoid hidden side effects.
- Prefer reusable functions.
- Validate required columns.
- Handle missing values explicitly.
- Export reproducible outputs.
- Do not hardcode absolute local paths.
- Use relative paths from the project root.
- Keep comments concise and useful.
- Use English for code identifiers.

### JavaScript

- Use modular functions.
- Avoid a single large unstructured file.
- Use async/await for JSON loading.
- Handle loading and error states.
- Keep DOM manipulation clear.
- Avoid heavy processing in the browser.
- Use English for code identifiers.

Suggested frontend functions:

```javascript
loadJson()
loadAllData()
renderSummaryCards()
renderFilters()
applyFilters()
renderYearlyChart()
renderMonthlyChart()
renderAnomaliesTable()
renderAnomaliesChart()
renderStationsMap()
formatNumber()
formatDate()
showErrorMessage()
```

---

## Error Handling

The frontend should handle missing JSON files gracefully.

Example:

```javascript
async function loadJson(path) {
  try {
    const response = await fetch(path);

    if (!response.ok) {
      throw new Error(`Could not load ${path}`);
    }

    return await response.json();
  } catch (error) {
    console.error(error);
    showErrorMessage("Data could not be loaded.");
    return null;
  }
}
```

The Python pipeline should fail clearly if required files or columns are missing.

---

## Commands

The project should be runnable locally with a simple command:

```bash
python scripts/main.py
```

This command should:

1. Load raw data.
2. Clean data.
3. Transform wide format to long format.
4. Generate daily aggregations.
5. Generate yearly trends.
6. Generate monthly trends.
7. Detect anomalies.
8. Export CSV files.
9. Export JSON files for the frontend.

---

## GitHub Pages

The static site must be deployed from:

```text
/docs
```

GitHub Pages configuration:

```text
Source: Deploy from branch
Branch: main
Folder: /docs
```

---

## README Requirements

The README must explain:

- What the project does.
- What problem it addresses.
- What data it uses.
- What methods it uses.
- How to run the pipeline.
- How the dashboard works.
- What the project does not solve.
- Ethical considerations.
- Data source.
- Acknowledgments.

---

## Important Limitations

Always communicate these limitations clearly:

- The project is historical and exploratory.
- The project is not a real-time alert system.
- The project does not predict future pollution.
- The project does not prove causes of pollution peaks.
- The project depends on official dataset quality.
- The project only represents areas covered by official monitoring stations.
- The project should not replace official environmental reports.

---

## Definition of Done

The project is considered complete when:

1. Raw data can be processed with one command.
2. Clean processed CSV files are generated.
3. Static JSON files are generated in `docs/data`.
4. Yearly trends are available.
5. Monthly trends are available.
6. Daily anomalies are available.
7. The static dashboard loads from GitHub Pages.
8. The dashboard shows summary cards.
9. The dashboard shows yearly trends.
10. The dashboard shows monthly trends.
11. The dashboard shows anomaly rankings.
12. The dashboard shows station information.
13. The dashboard explains the methodology and limitations.
14. The README is complete.
15. The project can be understood by someone reviewing it for the Building AI course.

---

## Suggested Repository Name

```text
aireba-trends
```

## Suggested Project Title

```text
AireBA Trends
```

## Suggested Subtitle

```text
Historical Air Quality Trends and Anomaly Detection for Buenos Aires
```
