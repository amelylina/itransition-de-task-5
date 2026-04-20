import streamlit as st
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
    if st.sidebar.button("Refresh data", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    # st.caption("Last-fetched timestamp: ") <-- Cool feature to add later !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    st.divider()
    st.header("Controls")
    chart_type = st.selectbox("Chart type", options=["Line", "Bar"])

try:
    df = load_data(csv_url)
    mines = get_mine_columns(df)
    
    st.success(f"Loaded {len(df)} days × {len(mines)} mines")

    if not mines:
        st.warning("No mines data in loaded CSV")
    else:
        df = ensure_total(df,mines)
        tab_names = ['Total'] + mines
        tabs = st.tabs(tab_names)

        for tab, name in zip(tabs,tab_names):
            with tab:
                render_mine_tab(name,df[name],chart_type)
    
    with st.expander("Raw data (debug)"):
        st.dataframe(df, width='stretch')

except Exception as e:
    st.error(f"Failed to load data: {e}")