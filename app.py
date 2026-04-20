import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

HELPER_COLS = {'DayOfWeek', 'DayMultiplier', 'TrendMultiplier', 'EventMultiplier'}
NON_MINE_COLS = HELPER_COLS | {'Total'}
DEFAULT_CSV_URL= "https://docs.google.com/spreadsheets/d/e/2PACX-1vQQkpBuxbA9Vago-goGN1T1pZsa1KrutI5lj85YU2nqFChPVT17DF7qKjaX_CBYdQXyQjE_NTSFWZuM/pub?gid=50105197&single=true&output=csv"

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
    st.caption("Last-fetched timestamp: ")
    
    st.divider()
    st.header("Controls")
    chart_type = st.selectbox("Chart type", options=["Line", "Bar"])

@st.cache_data(ttl=60, show_spinner="Fetching data...")
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    df = df.dropna(axis=1, how='all')
    df = df.drop(columns=[c for c in HELPER_COLS if c in df.columns])
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    df = df.set_index('Date')
    df = df.dropna(how='all')
    return df

def get_mine_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in NON_MINE_COLS]

def render_stats_cards(series: pd.Series):
    mean_val = series.mean()
    median_val = series.median()
    std_val = series.std()
    q1,q3 = np.percentile(series,[25,75])
    iqr_val = q3-q1

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("Mean", f"{mean_val:.2f}")
    col2.metric("Median", f"{median_val:.2f}")
    col3.metric("Std Dev", f"{std_val:.2f}")
    col4.metric("IQR", f"{iqr_val:.2f}")

def build_chart(name: str, series: pd.Series, chart_type: str = "Line")-> go.Figure:
    dates = series.index
    values = series.values
    fig = go.Figure()

    if chart_type == "Line":
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name=name,
            line=dict(width=2),
            marker=dict(size=5)
        ))
    elif chart_type == "Bar":
        fig.add_trace(go.Bar(
            x=dates,
            y=values,
            name=name
        ))

    fig.update_layout(
        title=f"{name}: Daily Output",
        xaxis_title="Date",
        yaxis_title="Output",
        hovermode='x unified',
        height=450,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig

def render_mine_tab(name: str, series: pd.Series,chart_type: str):
    st.subheader(name)
    render_stats_cards(series)
    fig = build_chart(name,series,chart_type)
    st.plotly_chart(fig,width="stretch")


try:
    df = load_data(csv_url)
    mines = get_mine_columns(df)
    
    st.success(f"Loaded {len(df)} days × {len(mines)} mines: {', '.join(mines)}")

    if not mines:
        st.warning("No mines data in loaded CSV")
    else:
        if "Total" not in df.columns:
            df["Total"] = df[mines].sum(axis=1)
        tab_names = ['Total'] + mines
        tabs = st.tabs(tab_names)

        for tab, name in zip(tabs,tab_names):
            with tab:
                render_mine_tab(name,df[name],chart_type)
    
    with st.expander("Raw data (debug)"):
        st.dataframe(df, width='stretch')

except Exception as e:
    st.error(f"Failed to load data: {e}")