from load_data import (
    load_air_quality_data,
    load_pollutants_data,
    load_stations_data,
)
from clean_data import (
    clean_air_quality_data,
    clean_pollutants_data,
    clean_stations_data,
)
from transform_data import aggregate_daily_values, transform_wide_to_long
from trend_analysis import calculate_monthly_trends, calculate_yearly_trends
from anomaly_detection import detect_daily_anomalies


def main() -> None:
    air_quality_df = clean_air_quality_data(load_air_quality_data())
    stations_df = clean_stations_data(load_stations_data())
    pollutants_df = clean_pollutants_data(load_pollutants_data())

    _ = pollutants_df

    long_df = transform_wide_to_long(air_quality_df, stations_df)
    daily_df = aggregate_daily_values(long_df)
    yearly_trends_df = calculate_yearly_trends(daily_df)
    monthly_trends_df = calculate_monthly_trends(daily_df)
    anomalies_df = detect_daily_anomalies(daily_df)

    print("Scaffold ready.")
    print(f"Long rows: {len(long_df)}")
    print(f"Daily rows: {len(daily_df)}")
    print(f"Yearly rows: {len(yearly_trends_df)}")
    print(f"Monthly rows: {len(monthly_trends_df)}")
    print(f"Anomalies rows: {len(anomalies_df)}")


if __name__ == "__main__":
    main()
