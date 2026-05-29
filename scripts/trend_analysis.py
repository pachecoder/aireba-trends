import pandas as pd


def calculate_yearly_trends(daily_df: pd.DataFrame) -> pd.DataFrame:
    if daily_df.empty:
        return pd.DataFrame()
    raise NotImplementedError("Yearly trend analysis is not implemented yet.")


def calculate_monthly_trends(daily_df: pd.DataFrame) -> pd.DataFrame:
    if daily_df.empty:
        return pd.DataFrame()
    raise NotImplementedError("Monthly trend analysis is not implemented yet.")
