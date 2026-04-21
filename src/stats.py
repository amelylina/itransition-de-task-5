import numpy as np
import pandas as pd
from scipy.stats import t as student_t

def compute_stats(series: pd.Series) -> dict:
    clean = series.dropna()
    if len(clean)==0:
        return {'mean': 0, 'median': 0, 'std': 0, 'iqr': 0, 'q1': 0, 'q3': 0} 
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
    rolling_mean = series.rolling(window=window, center=False, min_periods=1).mean()
    rolling_mean.replace(0, np.nan)
    pct_deviation = ((series - rolling_mean).abs()/rolling_mean)*100
    return pct_deviation > threshold

def detect_grubbs(series: pd.Series, alpha: float=0.05)-> pd.Series:
    remaining = series.copy()
    flagged_mask = pd.Series(False,index=series.index)
    while len(remaining)>=3:
        mean = remaining.mean()
        std = remaining.std()
        if std == 0:
            break

        deviations = (remaining-mean).abs()
        most_extreme_idx = deviations.idxmax()
        G= deviations.loc[most_extreme_idx]/std
        
        N = len(remaining)
        t_crit= student_t.ppf(1-alpha/(2*N), df=N-2)
        G_crit = ((N-1)/np.sqrt(N)*np.sqrt(t_crit**2/(N-2+t_crit**2)))

        if G>G_crit:
            flagged_mask.loc[most_extreme_idx]=True #type: ignore
            remaining = remaining.drop(most_extreme_idx)
        else:
            break

    return flagged_mask

def group_anomalies(mask: pd.Series) -> list[tuple]:
    if not mask.any():
        return []
    groups = (mask != mask.shift()).cumsum()
    runs = []
    for _, group_idx in mask[mask].groupby(groups[mask]):
        runs.append((group_idx.index.min(), group_idx.index.max()))
    return runs
