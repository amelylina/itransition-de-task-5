import streamlit as st
import pandas as pd
from src.stats import compute_stats
from src.charts import build_chart

def render_stats_cards(series: pd.Series):
    s = compute_stats(series)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mean", f"{s['mean']:.2f}")
    col2.metric("Median", f"{s['median']:.2f}")
    col3.metric("Std Dev", f"{s['std']:.2f}")
    col4.metric("IQR", f"{s['iqr']:.2f}")


def render_mine_tab(name: str, series: pd.Series, chart_type: str):
    st.subheader(name)
    render_stats_cards(series)
    fig = build_chart(name, series, chart_type=chart_type)
    st.plotly_chart(fig, width="stretch")