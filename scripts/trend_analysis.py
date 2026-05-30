import pandas as pd


def calculate_yearly_trends(daily_df: pd.DataFrame) -> pd.DataFrame:
    if daily_df.empty:
        return pd.DataFrame()
    yearly = (
        daily_df.groupby(["year", "station", "pollutant"], dropna=False)["daily_avg"]
        .agg(
            avg_value="mean",
            median_value="median",
            max_value="max",
            min_value="min",
            std_value="std",
            records_count="count",
        )
        .reset_index()
    )
    yearly["std_value"] = yearly["std_value"].fillna(0.0)
    numeric_columns = ["avg_value", "median_value", "max_value", "min_value", "std_value"]
    yearly[numeric_columns] = yearly[numeric_columns].round(4)
    yearly["records_count"] = yearly["records_count"].astype(int)
    return yearly.sort_values(["year", "station", "pollutant"]).reset_index(drop=True)


def calculate_monthly_trends(daily_df: pd.DataFrame) -> pd.DataFrame:
    if daily_df.empty:
        return pd.DataFrame()
    monthly = (
        daily_df.groupby(["year", "month", "station", "pollutant"], dropna=False)[
            "daily_avg"
        ]
        .agg(
            avg_value="mean",
            median_value="median",
            max_value="max",
            min_value="min",
            std_value="std",
            records_count="count",
        )
        .reset_index()
    )
    monthly["std_value"] = monthly["std_value"].fillna(0.0)
    numeric_columns = ["avg_value", "median_value", "max_value", "min_value", "std_value"]
    monthly[numeric_columns] = monthly[numeric_columns].round(4)
    monthly["records_count"] = monthly["records_count"].astype(int)
    return monthly.sort_values(["year", "month", "station", "pollutant"]).reset_index(
        drop=True
    )
