import streamlit as st
import pandas as pd
from src.config import DEFAULT_CSV_URL
from src.data import load_data, get_mine_columns, ensure_total
from src.ui import render_mine_tab

st.set_page_config(
    page_title="Weyland-Yutani Mining Ops",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Weyland-Yutani Mining Operations")
st.caption("Daily statistics and anomaly detection")

with st.sidebar:
    st.header("Data Source")
    csv_url = st.text_input("CSV URL", value=DEFAULT_CSV_URL)

try:
    df = load_data(csv_url)
except pd.errors.ParserError:
    st.error("The CSV could not be parsed. Is the URL pointing to a valid published CSV?")
    st.stop()
except (ConnectionError, TimeoutError):
    st.error("Could not reach the data source. Check your connection or the URL.")
    st.stop()
except Exception as e:
    st.error(f"Failed to load data: {e}. Analysis stopped.")
    st.stop()
    
with st.sidebar:
    if st.button("Refresh data", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    if 'fetched_at' in df.attrs:
        st.sidebar.caption(f"Data fetched: {df.attrs['fetched_at']}")
    st.divider()
    st.header("Controls")
    chart_type = st.selectbox("Chart type", options=["Line", "Bar", "Stacked"])
    trendline_degree = st.selectbox(
        "Trendline degree",
        options=[None, 1, 2, 3, 4],
        format_func=lambda x: "None" if x is None else f"Polynomial {x}",
    )

    st.divider()
    st.header("Anomaly Detection")
    with st.expander("IQR rule", expanded=True):
        iqr_enabled = st.checkbox("Enable IQR", value=False)
        iqr_k = st.slider("k multiplier", min_value=1.0, max_value=3.0, value=1.5, step=0.1)
    with st.expander("Z-score"):
        zscore_enabled = st.checkbox("Enable Z-score", value=False)
        zscore_threshold = st.slider("Threshold (σ)", min_value=1.0, max_value=4.0, value=3.0, step=0.1)
    with st.expander("Moving average"):
        ma_enabled = st.checkbox("Enable moving avg", value=False)
        ma_window = st.slider("Window (days)", min_value=3, max_value=21, value=7, step=2)
        ma_threshold = st.slider("Threshold (%)", min_value=5.0, max_value=50.0, value=20.0, step=1.0)
    with st.expander("Grubbs' test"):
        grubbs_enabled = st.checkbox("Enable Grubbs'", value=False)
        grubbs_alpha = st.slider("Significance α", min_value=0.01, max_value=0.10, value=0.05, step=0.01)

    st.divider()
    st.header("Debug")
    debug = st.checkbox("Show raw data table")

anomaly_params = {
    'iqr_enabled': iqr_enabled,
    'iqr_k': iqr_k,
    'zscore_enabled': zscore_enabled,
    'zscore_threshold': zscore_threshold,
    'ma_enabled': ma_enabled,
    'ma_window': ma_window,
    'ma_threshold': ma_threshold,
    'grubbs_enabled': grubbs_enabled,
    'grubbs_alpha': grubbs_alpha,
}

mines = get_mine_columns(df)
if not mines:
    st.warning("No mines data in loaded CSV")
    st.stop()
else:
    st.success(f"Loaded {len(df)} days × {len(mines)} mines.")
    df = ensure_total(df,mines)
    tab_names = ['Total'] + mines
    tabs = st.tabs(tab_names)

    for tab, name in zip(tabs,tab_names):
        with tab:
            render_mine_tab(
                name=name,
                series=df[name],
                chart_type=chart_type, 
                anomaly_params=anomaly_params,
                trendline_degree=trendline_degree, #type: ignore
                df=df,
                mines=mines
            )

if debug:
    with st.expander("Raw data (debug)"):
        st.dataframe(df, width='stretch')