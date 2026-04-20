import streamlit as st
import pandas as pd
from src.charts import build_chart, build_stacked_chart
from src.stats import compute_stats, detect_iqr, detect_zscore, detect_moving_avg, detect_grubbs

def compute_all_anomalies(series: pd.Series, params: dict)-> dict[str, pd.Series]:
    results = {}
    if params['iqr_enabled']:
        results['IQR'] = detect_iqr(series, params['iqr_k'])
    if params['zscore_enabled']:
        results['Z-score'] = detect_zscore(series, params['zscore_threshold'])
    if params['ma_enabled']:
        results['MovingAvg'] = detect_moving_avg(series, params['ma_window'], params['ma_threshold'])
    if params['grubbs_enabled']:
        results['Grubbs'] = detect_grubbs(series, params['grubbs_alpha'])
    return results

def render_mine_tab(
        name: str, 
        series: pd.Series, 
        chart_type: str, 
        anomaly_params: dict,
        trendline_degree: int,
        df: pd.DataFrame | None = None,
        mines: list[str] | None = None
):
    st.subheader(name)
    render_stats_cards(series)
    anomalies = compute_all_anomalies(series,anomaly_params)

    if chart_type == "Stacked" and name == "Total" and df is not None and mines is not None:
        fig = build_stacked_chart(df,mines)
    else:
        effective_chart_type = "Bar" if chart_type == "Stacked" else chart_type
        fig = build_chart(name, series, effective_chart_type, anomalies,trendline_degree)

    st.plotly_chart(fig, width="stretch")
    render_anomaly_table(series,anomalies)

def render_stats_cards(series: pd.Series):
    s = compute_stats(series)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mean", f"{s['mean']:.2f}")
    col2.metric("Median", f"{s['median']:.2f}")
    col3.metric("Std Dev", f"{s['std']:.2f}")
    col4.metric("IQR", f"{s['iqr']:.2f}")

def render_anomaly_table(series: pd.Series, anomalies: dict[str, pd.Series]):
    if not anomalies:
        st.caption("No anomaly tests were enabled in sidebar")
        return
    
    any_flagged = pd.Series(False, index=series.index)
    for mask in anomalies.values():
        any_flagged = any_flagged | mask
    if not any_flagged.any():
        st.caption("No anomalies detected")
        return
    
    rows = []
    for date in series.index[any_flagged]:
        row = {'Date':date, 'Value': f"{series.loc[date]:.2f}"}
        for test_name,mask in anomalies.items():
            row[test_name]="✓" if mask.loc[date] else ""
        rows.append(row)

    st.markdown("**Detected anomalies**")
    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)
