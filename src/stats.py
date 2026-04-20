import numpy as np
import pandas as pd

def compute_stats(series: pd.Series) -> dict:
    q1, q3 = np.percentile(series, [25, 75])
    return {
        'mean': series.mean(),
        'median': series.median(),
        'std': series.std(),
        'iqr': q3 - q1,
        'q1': q1,
        'q3': q3,
    }

def detect_iqr(series: pd.Series, k: float = 1.5)-> pd.Series:
    q1,q3 = np.percentile(series,[25,75])
    iqr = q3-q1
    lower = q1-k*iqr
    upper = q3+k*iqr
    return (series<lower) | (series>upper)

def detect_zscore(series: pd.Series, threshold: float = 3.0)-> pd.Series:
    mean = series.mean()
    std = series.std()
    if std == 0:
        return pd.Series(False,index=series.index)
    z_scores = (series-mean).abs() / std
    return z_scores > threshold

def detect_moving_avg(series: pd.Series, window: int=7, threshold: float=20.0)-> pd.Series:
    rolling_mean = series.rolling(window=window, center=True, min_periods=1).mean()
    pct_deviation = ((series - rolling_mean).abs()/rolling_mean)*100
    return pct_deviation > threshold