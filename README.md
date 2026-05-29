# aireba-trends

# AireBA Trends

Final project for the Building AI course

## Summary

AireBA Trends analyzes official air quality data from Buenos Aires City between 2009 and 2026. The project visualizes historical trends for NO2, CO and PM10 by monitoring station, and detects unusual daily pollution events using statistical methods and simple machine learning.

## Background

Air quality is an important urban issue. In large cities, pollution can change over time because of traffic, weather, urban activity and other environmental factors.

Buenos Aires City publishes official air quality datasets, but raw data is not always easy to understand. The information is useful, but it needs cleaning, aggregation and visualization to become more accessible.

This project tries to solve the following problems:

* Public air quality data is difficult to explore in raw format.
* Long-term pollution trends are not always easy to see.
* Unusual pollution peaks can be hidden inside large datasets.
* Citizens, students and researchers may need a simpler way to understand environmental data.

My personal motivation is to build a simple open source AI/data science project using real public data from Buenos Aires. I am interested in environmental data, open data, and practical machine learning that can help explain real-world problems.

This topic is important because air quality affects people’s daily life and health, especially children, older adults and people with respiratory conditions.

## How is it used?

The project is used as a static data analysis and visualization tool.

First, Python scripts process the official air quality datasets. The pipeline cleans the data, transforms it into a more useful format, calculates monthly and yearly trends, and detects daily anomalies.

Then, the project generates static JSON and CSV files that can be visualized in a simple dashboard hosted on GitHub Pages.

The dashboard can be used to answer questions such as:

* How did NO2 evolve over the years in each station?
* Which station had the highest PM10 values?
* Are there monthly patterns in CO, NO2 or PM10?
* Which days had unusual pollution peaks?
* Which pollutant had more extreme anomalies?

The main users could be:

* students
* citizens
* journalists
* researchers
* open data enthusiasts
* environmental organizations

The project is not a real-time alert system. It is a historical and exploratory analysis tool.

Example of the data processing flow:

```python
def main():
    raw_data = load_air_quality_data()
    stations = load_stations_data()

    clean_data = clean_and_normalize(raw_data)
    long_data = transform_wide_to_long(clean_data)
    enriched_data = merge_with_stations(long_data, stations)

    yearly_trends = calculate_yearly_trends(enriched_data)
    monthly_trends = calculate_monthly_trends(enriched_data)
    anomalies = detect_anomalies(enriched_data)

    export_static_files(yearly_trends, monthly_trends, anomalies)

main()
```

The expected architecture is:

```text
Official datasets
        ↓
Python data pipeline
        ↓
Clean CSV / JSON files
        ↓
Static frontend
        ↓
GitHub Pages dashboard
```

## Data sources and AI methods

The project uses official open data from the Government of Buenos Aires City.

The main datasets are:

| Dataset | Description |
| ------ | ----------- |
| Air quality measurements | Historical pollution measurements from 2009 to 2026 |
| Environmental stations | Location and description of monitoring stations |
| Pollutants | Description of measured pollutants |

The project focuses on three pollutants:

| Pollutant | Description |
| --------- | ----------- |
| NO2 | Nitrogen dioxide |
| CO | Carbon monoxide |
| PM10 | Particulate matter smaller than 10 micrometers |

The original data has columns such as:

```text
fecha
hora
co_centenario
no2_centenario
pm10_centenario
co_cordoba
no2_cordoba
pm10_cordoba
```

The pipeline transforms this wide format into a long format:

```text
date
hour
datetime
year
month
station
pollutant
value
latitude
longitude
zone
```

The main data analysis techniques are:

* data cleaning
* data normalization
* wide-to-long transformation
* monthly aggregation
* yearly aggregation
* rolling averages
* trend analysis
* anomaly detection

The AI / machine learning part is focused on anomaly detection.

The first version can use statistical baselines such as:

* Z-score
* IQR
* rolling mean and standard deviation

A simple unsupervised machine learning model can also be used:

* Isolation Forest

Isolation Forest is useful because the dataset does not have labels saying which days are anomalies. The model can learn which observations look normal and which ones look unusual.

The project does not need deep learning because the goal is not image recognition, speech processing or a complex prediction system. The data is structured and historical, so simple statistical methods and unsupervised machine learning are more appropriate and easier to explain.

## Challenges

This project has some important limitations.

First, the project does not prove the cause of pollution events. If the system detects an unusual peak, it only means that the value was rare compared with the historical pattern of the same station and pollutant.

For example, if PM10 is unusually high on a specific day, the project cannot automatically say if it was caused by traffic, weather, construction, fires or another event.

Second, the analysis depends on the quality and completeness of the official dataset. Missing values, sensor errors or changes in monitoring methods can affect the results.

Third, the project does not estimate the exact air quality of every street or neighborhood. It only uses official monitoring stations.

The project does not solve:

* real-time pollution alerts
* exact street-level pollution estimation
* causal explanation of pollution peaks
* medical recommendations
* government-level environmental policy decisions

Ethical considerations:

* The dashboard should not create panic.
* Anomalies should be presented as unusual values, not proven causes.
* The data source and limitations must be clearly explained.
* The project should not replace official environmental reports.

## What next?

The project could grow in several ways.

Future improvements could include:

* adding weather data such as temperature, humidity, wind and rain
* adding public event or traffic information
* comparing anomalies with external events
* building a better interactive dashboard
* publishing an automatic monthly report
* adding more pollutants if the data is available
* improving anomaly detection models
* adding explainability techniques
* creating a public API

To move the project forward, I would need more knowledge and support in:

* environmental science
* air pollution standards
* geospatial analysis
* time series analysis
* data visualization design
* validation of anomaly detection results

A more advanced version could combine air quality, weather and traffic data to better understand why some pollution peaks happen.

## Acknowledgments

This project uses official open data from the Government of Buenos Aires City.

Main data source:

* Buenos Aires City Open Data - Air Quality dataset

Open source tools and libraries planned for the project:

* Python
* Pandas
* NumPy
* Scikit-learn
* Matplotlib
* Plotly
* Leaflet.js
* GitHub Pages

This project was created as the final project for the Building AI course by Reaktor Innovations and the University of Helsinki.

The idea is inspired by open data, environmental analytics and practical machine learning for public interest.
