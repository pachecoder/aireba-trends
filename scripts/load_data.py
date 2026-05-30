from pathlib import Path
from typing import Callable, Iterable

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT_DIR / "data" / "raw"

AIR_QUALITY_FILE_PATTERNS = (
    "calidad-aire*.csv",
    "calidad_aire*.csv",
    "calidad-de-aire*.xlsx",
    "calidad-de-aire*.xls",
)
STATIONS_FILE_PATTERNS = ("estaciones-ambientales*.xlsx", "stations*.csv")
POLLUTANTS_FILE_PATTERNS = ("contaminantes*.xlsx", "pollutants*.csv")
NON_DATA_SHEET_NAMES = {"diccionario", "dictionary", "metadata", "metadatos"}


def _resolve_air_quality_source_priority(file_path: Path) -> int:
    name = file_path.name.lower()
    if "2026" in name:
        return 50
    if "2025" in name:
        return 40
    if "2019" in name:
        return 30
    if "2018" in name:
        return 20
    if "2017" in name:
        return 10
    return 0


def _discover_files(patterns: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(sorted(RAW_DIR.glob(pattern)))
    return list(dict.fromkeys(paths))


def _read_tabular_file(
    file_path: Path,
    include_source_metadata: bool = False,
    source_priority: int = 0,
) -> pd.DataFrame:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        dataframe = pd.read_csv(file_path)
    elif suffix in {".xlsx", ".xls"}:
        dataframe = _read_excel_data_sheet(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path.name}")

    if include_source_metadata:
        dataframe["__source_file"] = file_path.name
        dataframe["__source_priority"] = source_priority
    return dataframe


def _read_excel_data_sheet(file_path: Path) -> pd.DataFrame:
    workbook = pd.ExcelFile(file_path)
    preferred_sheets = [
        sheet_name
        for sheet_name in workbook.sheet_names
        if sheet_name.strip().lower() not in NON_DATA_SHEET_NAMES
    ]
    if not preferred_sheets:
        preferred_sheets = workbook.sheet_names
    return workbook.parse(preferred_sheets[0])


def _normalize_missing_values(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.copy()
    normalized = normalized.replace(
        {
            "s/d": pd.NA,
            "S/D": pd.NA,
            "sd": pd.NA,
            "SD": pd.NA,
            "": pd.NA,
        }
    )
    return normalized


def _drop_empty_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe
    return dataframe.dropna(how="all").reset_index(drop=True)


def _deduplicate_records(dataframes: list[pd.DataFrame]) -> pd.DataFrame:
    non_empty_frames = [df for df in dataframes if not df.empty]
    if not non_empty_frames:
        return pd.DataFrame()

    combined = pd.concat(non_empty_frames, ignore_index=True, sort=False)
    combined = _normalize_missing_values(combined)
    combined = _drop_empty_rows(combined)

    comparable_columns = [
        column
        for column in combined.columns
        if combined[column].notna().any()
    ]
    if not comparable_columns:
        return combined

    return combined.drop_duplicates(subset=comparable_columns).reset_index(drop=True)


def _load_dataset(
    patterns: Iterable[str],
    dataset_label: str,
    include_source_metadata: bool = False,
    priority_resolver: Callable[[Path], int] | None = None,
) -> pd.DataFrame:
    files = _discover_files(patterns)
    if not files:
        raise FileNotFoundError(f"No raw files found for {dataset_label} in {RAW_DIR}")

    dataframes = [
        _read_tabular_file(
            file_path,
            include_source_metadata=include_source_metadata,
            source_priority=priority_resolver(file_path) if priority_resolver else 0,
        )
        for file_path in files
    ]
    return _deduplicate_records(dataframes)


def load_air_quality_data() -> pd.DataFrame:
    return _load_dataset(
        AIR_QUALITY_FILE_PATTERNS,
        "air quality",
        include_source_metadata=True,
        priority_resolver=_resolve_air_quality_source_priority,
    )


def load_stations_data() -> pd.DataFrame:
    return _load_dataset(STATIONS_FILE_PATTERNS, "stations")


def load_pollutants_data() -> pd.DataFrame:
    return _load_dataset(POLLUTANTS_FILE_PATTERNS, "pollutants")
