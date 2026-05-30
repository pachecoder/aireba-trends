import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


MIN_GROUP_SIZE_FOR_IFOREST = 90
IFOREST_CONTAMINATION = 0.03
IFOREST_RANDOM_STATE = 42


def _build_temporal_features(group: pd.DataFrame) -> pd.DataFrame:
    working = group.sort_values("date").copy()
    working["day_of_week"] = pd.to_datetime(working["date"]).dt.dayofweek
    working["rolling_mean_7d"] = working["daily_avg"].rolling(7, min_periods=1).mean()
    working["rolling_mean_30d"] = working["daily_avg"].rolling(30, min_periods=1).mean()
    working["rolling_std_30d"] = (
        working["daily_avg"].rolling(30, min_periods=2).std().fillna(0.0)
    )
    return working


def _run_isolation_forest(group: pd.DataFrame) -> pd.DataFrame:
    working = _build_temporal_features(group)
    working["iforest_score"] = 0.0
    working["iforest_is_anomaly"] = False

    if len(working) < MIN_GROUP_SIZE_FOR_IFOREST:
        return working

    feature_columns = [
        "daily_avg",
        "month",
        "year",
        "day_of_week",
        "rolling_mean_7d",
        "rolling_mean_30d",
        "rolling_std_30d",
    ]
    feature_frame = working[feature_columns].fillna(0.0)

    model = IsolationForest(
        contamination=IFOREST_CONTAMINATION,
        random_state=IFOREST_RANDOM_STATE,
    )
    predictions = model.fit_predict(feature_frame)
    scores = -model.score_samples(feature_frame)

    working["iforest_score"] = scores
    working["iforest_is_anomaly"] = predictions == -1
    return working


def _classify_severity(
    actual_value: float,
    moderate_threshold: float,
    extreme_threshold: float,
    z_score: float,
    iforest_is_relevant: bool,
) -> str:
    abs_z_score = abs(z_score)
    if actual_value > extreme_threshold:
        return "Extreme"
    if actual_value > moderate_threshold:
        if z_score >= 3 or iforest_is_relevant:
            return "High"
        return "Moderate"
    if iforest_is_relevant and abs_z_score >= 3:
        return "High"
    if iforest_is_relevant and abs_z_score >= 2:
        return "Moderate"
    return "Normal"


def detect_daily_anomalies(daily_df: pd.DataFrame) -> pd.DataFrame:
    if daily_df.empty:
        return pd.DataFrame()

    frames: list[pd.DataFrame] = []

    for (_, _), group in daily_df.groupby(["station", "pollutant"], dropna=False):
        working = _run_isolation_forest(group)

        q1 = working["daily_avg"].quantile(0.25)
        median = working["daily_avg"].median()
        q3 = working["daily_avg"].quantile(0.75)
        iqr = q3 - q1
        moderate_threshold = q3 + 1.5 * iqr
        extreme_threshold = q3 + 3.0 * iqr

        mean_value = working["daily_avg"].mean()
        std_value = working["daily_avg"].std()
        if pd.isna(std_value) or std_value == 0:
            working["z_score"] = 0.0
        else:
            working["z_score"] = (working["daily_avg"] - mean_value) / std_value

        working["actual_value"] = working["daily_avg"]
        working["expected_value"] = median
        working["difference"] = working["actual_value"] - working["expected_value"]
        working["percentage_difference"] = (
            working["difference"] / working["expected_value"].replace(0, pd.NA) * 100
        ).fillna(0.0)

        working["iqr_is_anomaly"] = working["actual_value"] > moderate_threshold
        working["iforest_is_relevant"] = working["iforest_is_anomaly"] & (
            working["z_score"].abs() >= 2
        )
        working["is_anomaly"] = (
            working["iqr_is_anomaly"] | working["iforest_is_relevant"]
        )
        working["method"] = np.where(
            working["iqr_is_anomaly"] & working["iforest_is_relevant"],
            "IQR + Isolation Forest",
            np.where(working["iforest_is_relevant"], "Isolation Forest", "IQR"),
        )
        working["severity"] = working.apply(
            lambda row: _classify_severity(
                actual_value=row["actual_value"],
                moderate_threshold=moderate_threshold,
                extreme_threshold=extreme_threshold,
                z_score=row["z_score"],
                iforest_is_relevant=bool(row["iforest_is_relevant"]),
            ),
            axis=1,
        )
        frames.append(working)

    anomalies = pd.concat(frames, ignore_index=True)
    anomalies = anomalies[
        anomalies["is_anomaly"] & (anomalies["severity"] != "Normal")
    ].copy()
    anomalies = anomalies[
        [
            "date",
            "station",
            "pollutant",
            "actual_value",
            "expected_value",
            "difference",
            "percentage_difference",
            "z_score",
            "method",
            "severity",
            "is_anomaly",
        ]
    ]

    numeric_columns = [
        "actual_value",
        "expected_value",
        "difference",
        "percentage_difference",
        "z_score",
    ]
    anomalies[numeric_columns] = anomalies[numeric_columns].round(4)
    anomalies["date"] = pd.to_datetime(anomalies["date"]).dt.strftime("%Y-%m-%d")
    severity_order = {"Moderate": 1, "High": 2, "Extreme": 3}
    anomalies["severity_rank"] = anomalies["severity"].map(severity_order).fillna(0)
    anomalies["abs_percentage_difference"] = anomalies[
        "percentage_difference"
    ].abs()
    anomalies = anomalies.sort_values(
        ["date", "severity_rank", "abs_percentage_difference"],
        ascending=[False, False, False],
    ).drop(columns=["severity_rank", "abs_percentage_difference"])
    return anomalies.reset_index(drop=True)
