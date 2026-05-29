from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"


def load_air_quality_data() -> pd.DataFrame:
    file_path = RAW_DIR / "air_quality.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Missing raw dataset: {file_path}")
    return pd.read_csv(file_path)


def load_stations_data() -> pd.DataFrame:
    file_path = RAW_DIR / "stations.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Missing stations dataset: {file_path}")
    return pd.read_csv(file_path)


def load_pollutants_data() -> pd.DataFrame:
    file_path = RAW_DIR / "pollutants.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Missing pollutants dataset: {file_path}")
    return pd.read_csv(file_path)
