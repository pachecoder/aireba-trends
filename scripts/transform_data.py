import pandas as pd


TARGET_POLLUTANTS = {"no2", "co", "pm10"}


def transform_wide_to_long(
    air_quality_df: pd.DataFrame, stations_df: pd.DataFrame
) -> pd.DataFrame:
    _ = stations_df
    if air_quality_df.empty:
        return pd.DataFrame()
    raise NotImplementedError("Wide-to-long transformation is not implemented yet.")


def aggregate_daily_values(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return pd.DataFrame()
    raise NotImplementedError("Daily aggregation is not implemented yet.")
