from dataclasses import dataclass

HELPER_COLS = {'DayOfWeek', 'DayMultiplier', 'TrendMultiplier', 'EventMultiplier'}
NON_MINE_COLS = HELPER_COLS | {'Total'}

DEFAULT_CSV_URL= "https://docs.google.com/spreadsheets/d/e/2PACX-1vQQkpBuxbA9Vago-goGN1T1pZsa1KrutI5lj85YU2nqFChPVT17DF7qKjaX_CBYdQXyQjE_NTSFWZuM/pub?gid=50105197&single=true&output=csv"

@dataclass
class AnomalyParams:
    iqr_enabled: bool = False
    iqr_k: float = 1.5
    zscore_enabled: bool = False
    zscore_threshold: float = 3.0
    ma_enabled: bool = False
    ma_window: int = 7
    ma_threshold: float = 20.0
    grubbs_enabled: bool = False
    grubbs_alpha: float = 0.05