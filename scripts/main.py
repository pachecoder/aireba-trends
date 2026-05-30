import pandas as pd

from export_static_data import export_csv, export_json, export_json_object
from load_data import (
    load_air_quality_data,
    load_pollutants_data,
    load_stations_data,
)
from clean_data import (
    clean_air_quality_data,
    consolidate_air_quality_observations,
    clean_pollutants_data,
    clean_stations_data,
)
from transform_data import aggregate_daily_values, transform_wide_to_long
from trend_analysis import calculate_monthly_trends, calculate_yearly_trends
from anomaly_detection import detect_daily_anomalies


def build_station_summary(long_df):
    summary = (
        long_df.groupby("station", dropna=False)
        .agg(
            pollutants=(
                "pollutant",
                lambda values: ", ".join(sorted(values.dropna().unique())),
            ),
            pollutants_count=("pollutant", "nunique"),
            first_date=("date", "min"),
            latest_date=("date", "max"),
            records_count=("value", "count"),
        )
        .reset_index()
    )
    summary["first_date"] = pd.to_datetime(summary["first_date"]).dt.strftime("%Y-%m-%d")
    summary["latest_date"] = pd.to_datetime(summary["latest_date"]).dt.strftime(
        "%Y-%m-%d"
    )
    return summary


def build_pollutant_summary(daily_df):
    return (
        daily_df.groupby("pollutant", dropna=False)
        .agg(
            stations_count=("station", "nunique"),
            avg_daily_value=("daily_avg", "mean"),
            max_daily_value=("daily_max", "max"),
            min_daily_value=("daily_min", "min"),
            daily_records_count=("daily_avg", "count"),
            source_records_count=("records_count", "sum"),
        )
        .reset_index()
        .round(
            {
                "avg_daily_value": 4,
                "max_daily_value": 4,
                "min_daily_value": 4,
            }
        )
    )


def build_summary(long_df, daily_df, anomalies_df, stations_df, overlap_report_df):
    anomaly_rate_daily = (
        len(anomalies_df) / len(daily_df) * 100 if len(daily_df) else 0.0
    )
    return {
        "project_name": "AireBA Trends",
        "period_start": int(long_df["year"].min()),
        "period_end": int(long_df["year"].max()),
        "latest_available_date": str(long_df["date"].max().date()),
        "pollutants": sorted(long_df["pollutant"].dropna().unique().tolist()),
        "stations_count": int(stations_df["station"].nunique()),
        "total_records": int(len(long_df)),
        "anomalies_detected": int(len(anomalies_df)),
        "daily_records": int(len(daily_df)),
        "anomaly_rate_daily_pct": round(anomaly_rate_daily, 2),
        "anomaly_rate_note": "The anomaly count is measured against daily aggregated records, not hourly records.",
        "overlap_groups_resolved": int(len(overlap_report_df)),
    }


def build_metadata(pollutants_df):
    units = {
        row["pollutant"]: row["unit"]
        for row in pollutants_df.to_dict(orient="records")
        if row.get("pollutant") and row.get("unit")
    }
    return {
        "project_name": "AireBA Trends",
        "data_source": "Official open data from the Government of Buenos Aires City.",
        "methodology": "Air quality records are normalized from wide to long format, non-positive pollutant placeholders are removed, values are aggregated to daily level, and each station-pollutant series is analyzed with an IQR statistical baseline plus Isolation Forest when enough history exists.",
        "limitations": [
            "This project is historical and exploratory.",
            "This project is not a real-time alert system.",
            "This project does not predict future pollution.",
            "This project does not prove causes of pollution peaks.",
            "This project depends on official dataset quality.",
        ],
        "anomaly_methods": [
            "IQR baseline on daily averages by station and pollutant.",
            "Isolation Forest on temporal features such as day of week and rolling windows when enough data is available.",
            "Isolation Forest flags are kept as anomalies only when the absolute z-score is at least 2, to avoid reporting weak model-only points as unusual events.",
        ],
        "anomaly_rate_note": "Percentages for detected anomalies should be interpreted over the daily aggregated table because anomaly detection runs on daily records, not on the hourly long table.",
        "units": units,
        "pollutants": pollutants_df.to_dict(orient="records"),
    }


def main() -> None:
    air_quality_df = clean_air_quality_data(load_air_quality_data())
    air_quality_df, overlap_report_df = consolidate_air_quality_observations(
        air_quality_df
    )
    stations_df = clean_stations_data(load_stations_data())
    pollutants_df = clean_pollutants_data(load_pollutants_data())

    long_df = transform_wide_to_long(air_quality_df, stations_df)
    daily_df = aggregate_daily_values(long_df)
    yearly_trends_df = calculate_yearly_trends(daily_df)
    monthly_trends_df = calculate_monthly_trends(daily_df)
    anomalies_df = detect_daily_anomalies(daily_df)
    station_summary_df = build_station_summary(long_df)
    pollutant_summary_df = build_pollutant_summary(daily_df)

    export_csv(long_df, "air_quality_long.csv")
    export_csv(daily_df, "daily_air_quality.csv")
    export_csv(yearly_trends_df, "yearly_trends.csv")
    export_csv(monthly_trends_df, "monthly_trends.csv")
    export_csv(anomalies_df, "anomalies.csv")
    export_csv(station_summary_df, "station_summary.csv")
    export_csv(pollutant_summary_df, "pollutant_summary.csv")
    export_csv(overlap_report_df, "source_overlap_report.csv")

    export_json(yearly_trends_df, "yearly_trends.json")
    export_json(monthly_trends_df, "monthly_trends.json")
    export_json(anomalies_df, "anomalies.json")
    export_json(stations_df[["station", "latitude", "longitude", "address", "zone", "pollutants"]], "stations.json")
    export_json_object(
        build_summary(long_df, daily_df, anomalies_df, stations_df, overlap_report_df),
        "summary.json",
    )
    export_json_object(build_metadata(pollutants_df), "metadata.json")

    print("Pipeline completed.")
    print(f"Overlap groups resolved: {len(overlap_report_df)}")
    print(f"Long rows: {len(long_df)}")
    print(f"Daily rows: {len(daily_df)}")
    print(f"Yearly rows: {len(yearly_trends_df)}")
    print(f"Monthly rows: {len(monthly_trends_df)}")
    print(f"Anomalies rows: {len(anomalies_df)}")


if __name__ == "__main__":
    main()
