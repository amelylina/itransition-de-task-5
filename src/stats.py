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