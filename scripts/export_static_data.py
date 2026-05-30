import json
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
DOCS_DATA_DIR = ROOT_DIR / "docs" / "data"


def ensure_output_directories() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DATA_DIR.mkdir(parents=True, exist_ok=True)


def export_csv(dataframe: pd.DataFrame, filename: str) -> Path:
    ensure_output_directories()
    output_path = PROCESSED_DIR / filename
    dataframe.to_csv(output_path, index=False)
    return output_path


def export_json(dataframe: pd.DataFrame, filename: str) -> Path:
    ensure_output_directories()
    output_path = DOCS_DATA_DIR / filename
    dataframe.to_json(output_path, orient="records", indent=2, force_ascii=False)
    return output_path


def export_json_object(payload: dict | list, filename: str) -> Path:
    ensure_output_directories()
    output_path = DOCS_DATA_DIR / filename
    with output_path.open("w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, ensure_ascii=False, indent=2)
    return output_path
