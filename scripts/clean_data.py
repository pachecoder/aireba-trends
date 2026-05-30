import pandas as pd


TARGET_POLLUTANTS = {"co", "no2", "pm10"}
STATION_DISPLAY_NAMES = {
    "la_boca": "La Boca",
    "centenario": "Centenario",
    "cordoba": "Córdoba",
    "palermo": "Palermo",
}


def _fix_text_encoding(value: object) -> object:
    if not isinstance(value, str):
        return value
    try:
        return value.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def _normalize_text_value(value: object) -> object:
    if not isinstance(value, str):
        return value
    normalized = _fix_text_encoding(value).strip()
    if normalized.lower() in {"", "s/d", "sd", "nan", "none"}:
        return pd.NA
    return normalized


def _normalize_numeric_series(series: pd.Series) -> pd.Series:
    cleaned = series.astype("string").str.strip().str.replace(",", ".", regex=False)
    cleaned = cleaned.replace({"<NA>": pd.NA, "nan": pd.NA, "None": pd.NA})
    return pd.to_numeric(cleaned, errors="coerce")


def _parse_air_quality_date(series: pd.Series) -> pd.Series:
    as_string = series.astype("string").str.strip()
    parsed = pd.to_datetime(as_string, format="%d%b%Y:%H:%M:%S", errors="coerce")
    fallback = pd.to_datetime(as_string, format="%Y-%m-%d", errors="coerce")
    parsed = parsed.fillna(fallback)
    if parsed.isna().any():
        remaining = as_string[parsed.isna()].dropna().unique().tolist()
        raise ValueError(f"Unsupported air quality dates: {remaining[:5]}")
    return parsed


def _normalize_station_name(value: object) -> object:
    normalized = _normalize_text_value(value)
    if not isinstance(normalized, str):
        return normalized
    return normalized.lower().replace(" ", "_")


def _format_station_display_name(value: object) -> object:
    station_key = _normalize_station_name(value)
    if not isinstance(station_key, str):
        return value
    return STATION_DISPLAY_NAMES.get(
        station_key,
        " ".join(part.capitalize() for part in station_key.split("_")),
    )


def standardize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    cleaned = dataframe.copy()
    cleaned.columns = (
        cleaned.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
    )
    if cleaned.columns.duplicated().any():
        merged_columns: dict[str, pd.Series] = {}
        ordered_names: list[str] = []
        for column_name in cleaned.columns.unique():
            duplicated = cleaned.loc[:, cleaned.columns == column_name]
            if isinstance(duplicated, pd.Series):
                merged_columns[column_name] = duplicated
            else:
                merged_columns[column_name] = duplicated.bfill(axis=1).iloc[:, 0]
            ordered_names.append(column_name)
        cleaned = pd.DataFrame(merged_columns)
        cleaned = cleaned[ordered_names]
    return cleaned


def clean_air_quality_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    cleaned = standardize_columns(dataframe)
    cleaned = cleaned.rename(columns={"ï»¿fecha": "fecha"})
    cleaned = cleaned.apply(lambda column: column.map(_normalize_text_value))

    required_columns = {"fecha", "hora"}
    missing_columns = required_columns - set(cleaned.columns)
    if missing_columns:
        raise ValueError(f"Missing required air quality columns: {sorted(missing_columns)}")

    cleaned["date"] = _parse_air_quality_date(cleaned["fecha"]).dt.normalize()
    cleaned["hora"] = pd.to_numeric(cleaned["hora"], errors="coerce").astype("Int64")
    cleaned = cleaned[cleaned["hora"].between(1, 24, inclusive="both")].copy()
    cleaned["hour"] = cleaned["hora"].astype(int)
    cleaned["datetime"] = cleaned["date"] + pd.to_timedelta(cleaned["hour"] - 1, unit="h")
    cleaned["year"] = cleaned["date"].dt.year.astype(int)
    cleaned["month"] = cleaned["date"].dt.month.astype(int)
    cleaned["day"] = cleaned["date"].dt.day.astype(int)

    measurement_columns = [
        column
        for column in cleaned.columns
        if "_" in column and column.split("_", 1)[0] in TARGET_POLLUTANTS
    ]
    for column in measurement_columns:
        cleaned[column] = _normalize_numeric_series(cleaned[column])

    cleaned = cleaned.drop(columns=["fecha", "hora"]).drop_duplicates().reset_index(drop=True)
    return cleaned


def consolidate_air_quality_observations(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if dataframe.empty:
        return dataframe, pd.DataFrame()

    working = dataframe.copy()
    measurement_columns = [
        column
        for column in working.columns
        if "_" in column and column.split("_", 1)[0] in TARGET_POLLUTANTS
    ]
    working["__source_priority"] = pd.to_numeric(
        working.get("__source_priority", 0), errors="coerce"
    ).fillna(0)
    working["__filled_measurements"] = working[measurement_columns].notna().sum(axis=1)
    working = working.sort_values(
        ["date", "hour", "__source_priority", "__filled_measurements"],
        ascending=[True, True, False, False],
    )

    key_columns = ["date", "hour"]
    duplicated_mask = working.duplicated(subset=key_columns, keep=False)
    if not duplicated_mask.any():
        consolidated = working.drop(columns=["__source_file", "__source_priority"], errors="ignore")
        return consolidated.reset_index(drop=True), pd.DataFrame()

    unique_rows = working.loc[~duplicated_mask].drop(
        columns=["__source_file", "__source_priority", "__filled_measurements"],
        errors="ignore",
    )
    duplicate_rows = working.loc[duplicated_mask].copy()
    report_rows: list[dict] = []
    consolidated_rows: list[dict] = []
    passthrough_columns = ["datetime", "year", "month", "day"]

    for (date_value, hour_value), group in duplicate_rows.groupby(key_columns, sort=True):
        base_row = {
            "date": date_value,
            "hour": int(hour_value),
        }

        for column in passthrough_columns + ["__source_file", "__source_priority"]:
            non_null_values = group[column].dropna()
            base_row[column] = non_null_values.iloc[0] if not non_null_values.empty else pd.NA

        for column in measurement_columns:
            non_null_values = group[column].dropna()
            base_row[column] = non_null_values.iloc[0] if not non_null_values.empty else pd.NA

        consolidated_rows.append(base_row)

        conflicting_columns = []
        for column in measurement_columns:
            distinct_values = pd.unique(group[column].dropna())
            if len(distinct_values) > 1:
                conflicting_columns.append(column)

        source_files = [str(item) for item in pd.unique(group["__source_file"].dropna())]
        report_rows.append(
            {
                "date": date_value,
                "hour": int(hour_value),
                "rows_merged": int(len(group)),
                "source_count": int(len(source_files)),
                "source_files": " | ".join(source_files),
                "max_source_priority": int(group["__source_priority"].max()),
                "min_filled_measurements": int(group["__filled_measurements"].min()),
                "max_filled_measurements": int(group["__filled_measurements"].max()),
                "conflicting_measurements_count": int(len(conflicting_columns)),
                "conflicting_measurements": " | ".join(conflicting_columns),
                "resolution_strategy": "first non-null by source priority and completeness",
            }
        )

    consolidated_duplicates = pd.DataFrame(consolidated_rows)
    report = pd.DataFrame(report_rows)
    consolidated = pd.concat([unique_rows, consolidated_duplicates], ignore_index=True, sort=False)
    consolidated = consolidated.drop(
        columns=["__source_file", "__source_priority", "__filled_measurements"],
        errors="ignore",
    ).reset_index(
        drop=True
    )
    return consolidated, report


def clean_stations_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    cleaned = standardize_columns(dataframe)
    cleaned = cleaned.apply(lambda column: column.map(_normalize_text_value))
    cleaned = cleaned.rename(
        columns={
            "nombre": "station",
            "direccion": "address",
            "zona_de_emplazamiento": "zone",
            "lat": "latitude",
            "long": "longitude",
            "parametrios_medidos": "pollutants",
        }
    )

    required_columns = {"station", "latitude", "longitude"}
    missing_columns = required_columns - set(cleaned.columns)
    if missing_columns:
        raise ValueError(f"Missing required stations columns: {sorted(missing_columns)}")

    cleaned["station"] = cleaned["station"].map(_format_station_display_name).astype("string")
    cleaned["station_key"] = cleaned["station"].map(_normalize_station_name)
    cleaned["address"] = cleaned.get("address", pd.Series(dtype="object")).map(
        _fix_text_encoding
    )
    cleaned["zone"] = cleaned.get("zone", pd.Series(dtype="object")).map(_fix_text_encoding)
    cleaned["latitude"] = _normalize_numeric_series(cleaned["latitude"])
    cleaned["longitude"] = _normalize_numeric_series(cleaned["longitude"])
    cleaned["pollutants"] = cleaned.get("pollutants", pd.Series(dtype="object")).fillna("")
    cleaned["pollutants"] = cleaned["pollutants"].map(
        lambda value: sorted(
            {
                item.strip().upper()
                for item in str(_fix_text_encoding(value)).split(",")
                if item and item.strip().upper() in {item.upper() for item in TARGET_POLLUTANTS}
            }
        )
        if pd.notna(value)
        else []
    )

    cleaned = cleaned.drop_duplicates(subset=["station_key"]).reset_index(drop=True)
    return cleaned


def clean_pollutants_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    cleaned = standardize_columns(dataframe)
    cleaned = cleaned.apply(lambda column: column.map(_normalize_text_value))
    cleaned = cleaned.rename(columns={"nombre": "pollutant", "descripcion": "description"})

    required_columns = {"pollutant", "description"}
    missing_columns = required_columns - set(cleaned.columns)
    if missing_columns:
        raise ValueError(f"Missing required pollutants columns: {sorted(missing_columns)}")

    cleaned["pollutant"] = cleaned["pollutant"].astype("string").str.upper().str.strip()
    cleaned["description"] = cleaned["description"].map(_fix_text_encoding)

    def extract_unit(description: object) -> object:
        if not isinstance(description, str):
            return pd.NA
        if "ppm" in description.lower():
            return "ppm"
        if "ppb" in description.lower():
            return "ppb"
        if "µg/m3" in description.lower() or "ug/m3" in description.lower():
            return "ug/m3"
        return pd.NA

    cleaned["unit"] = cleaned["description"].map(extract_unit)
    cleaned = cleaned[cleaned["pollutant"].str.lower().isin(TARGET_POLLUTANTS)].copy()
    cleaned = cleaned.drop_duplicates(subset=["pollutant"]).reset_index(drop=True)
    return cleaned
