import pandas as pd


def standardize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    cleaned = dataframe.copy()
    cleaned.columns = (
        cleaned.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
    )
    return cleaned


def clean_air_quality_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    return standardize_columns(dataframe)


def clean_stations_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    return standardize_columns(dataframe)


def clean_pollutants_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    return standardize_columns(dataframe)
