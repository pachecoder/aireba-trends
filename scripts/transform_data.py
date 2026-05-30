import pandas as pd


TARGET_POLLUTANTS = {"no2", "co", "pm10"}


def transform_wide_to_long(
    air_quality_df: pd.DataFrame, stations_df: pd.DataFrame
) -> pd.DataFrame:
    if air_quality_df.empty:
        return pd.DataFrame()

    id_columns = ["datetime", "date", "year", "month", "day", "hour"]
    value_columns = [
        column
        for column in air_quality_df.columns
        if "_" in column and column.split("_", 1)[0] in TARGET_POLLUTANTS
    ]

    long_df = air_quality_df.melt(
        id_vars=id_columns,
        value_vars=value_columns,
        var_name="measurement",
        value_name="value",
    )
    long_df = long_df.dropna(subset=["value"]).copy()
    long_df[["pollutant", "station"]] = long_df["measurement"].str.split(
        "_", n=1, expand=True
    )
    long_df["pollutant"] = long_df["pollutant"].str.upper()

    stations_lookup = stations_df[
        ["station_key", "station", "latitude", "longitude", "zone"]
    ].rename(columns={"station_key": "station", "station": "station_name"})
    long_df = long_df.merge(stations_lookup, on="station", how="left", suffixes=("", "_meta"))
    long_df["station"] = long_df["station_name"].fillna(
        long_df["station"].str.replace("_", " ").str.title()
    )
    long_df["station"] = long_df["station"].replace({"Cordoba": "Córdoba", "La Boca": "La Boca"})
    long_df = long_df.drop(columns=["measurement", "station_name"])
    long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")
    long_df = long_df.dropna(subset=["value"]).reset_index(drop=True)

    ordered_columns = [
        "datetime",
        "date",
        "year",
        "month",
        "day",
        "hour",
        "station",
        "pollutant",
        "value",
        "latitude",
        "longitude",
        "zone",
    ]
    return long_df[ordered_columns].drop_duplicates().reset_index(drop=True)


def aggregate_daily_values(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return pd.DataFrame()
    aggregated = (
        long_df.groupby(
            ["date", "year", "month", "station", "pollutant"], dropna=False
        )["value"]
        .agg(
            daily_avg="mean",
            daily_min="min",
            daily_max="max",
            daily_median="median",
            daily_std="std",
            records_count="count",
        )
        .reset_index()
    )
    aggregated["daily_std"] = aggregated["daily_std"].fillna(0.0)
    numeric_columns = [
        "daily_avg",
        "daily_min",
        "daily_max",
        "daily_median",
        "daily_std",
    ]
    aggregated[numeric_columns] = aggregated[numeric_columns].round(4)
    aggregated["records_count"] = aggregated["records_count"].astype(int)
    return aggregated.sort_values(["date", "station", "pollutant"]).reset_index(drop=True)
