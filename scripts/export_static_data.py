from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
DOCS_DATA_DIR = ROOT_DIR / "docs" / "data"


def export_csv(dataframe: pd.DataFrame, filename: str) -> Path:
    output_path = PROCESSED_DIR / filename
    dataframe.to_csv(output_path, index=False)
    return output_path


def export_json(dataframe: pd.DataFrame, filename: str) -> Path:
    output_path = DOCS_DATA_DIR / filename
    dataframe.to_json(output_path, orient="records", indent=2)
    return output_path
