import pandas as pd
import streamlit as st
from datetime import datetime
from src.config import HELPER_COLS, NON_MINE_COLS

@st.cache_data(ttl=60, show_spinner="Fetching data...")
def load_data(url: str, refresh_token: int) -> pd.DataFrame:
    df = pd.read_csv(url)
    df = df.dropna(axis=1, how='all')
    df = df.drop(columns=[c for c in HELPER_COLS if c in df.columns])
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    df = df.set_index('Date')
    df = df.dropna(how='all')
    df.attrs['fetched_at'] = datetime.now().strftime('%H:%M:%S')
    return df

def get_mine_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in NON_MINE_COLS]

def ensure_total(df: pd.DataFrame, mines: list[str]) -> pd.DataFrame:
    if "Total" not in df.columns:
        df = df.copy()
        df["Total"] = df[mines].sum(axis=1)
    return df
