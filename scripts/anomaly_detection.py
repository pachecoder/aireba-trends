import pandas as pd


def detect_daily_anomalies(daily_df: pd.DataFrame) -> pd.DataFrame:
    if daily_df.empty:
        return pd.DataFrame()
    raise NotImplementedError("Anomaly detection is not implemented yet.")
