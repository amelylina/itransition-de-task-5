import pandas as pd
import numpy as np
import plotly.graph_objects as go

def compute_trendline(series: pd.Series, degree: int)-> np.ndarray:
    x = np.arange(len(series))
    y = series.values
    coeffs = np.polyfit(x, y, degree) #type: ignore
    return np.polyval(coeffs, x)

def build_chart(
        name: str, 
        series: pd.Series, 
        chart_type: str = "Line",
        anomalies: dict[str, pd.Series] | None = None,
        trendline_degree: int | None = None
)-> go.Figure:
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

    if trendline_degree:
        trend_y = compute_trendline(series, trendline_degree)
        fig.add_trace(go.Scatter(
            x=dates,
            y=trend_y,
            mode='lines',
            name=f"Trend (degree {trendline_degree})",
            line=dict(width=3, dash='dash', color='#34495e'),
        ))

    if anomalies:
        colors = {
            'IQR': '#e74c3c', 
            'Z-score': '#f39c12', 
            'MovingAvg': "#e218ed",
            'Grubbs': "#1ee1c1",
        }
        for test_name, mask in anomalies.items():
            if not mask.any():
                continue
            flagged_dates = series.index[mask]
            flagged_values = series[mask].values
            fig.add_trace(go.Scatter(
                x=flagged_dates,
                y=flagged_values,
                mode='markers',
                name=f"{test_name} anomaly",
                marker=dict(
                    size=12,
                    color=colors.get(test_name, 'red'),
                    symbol='circle-open',
                    line=dict(width=2),
                ),
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

def build_stacked_chart(df: pd.DataFrame, mines: list[str])-> go.Figure:
    fig = go.Figure()
    for mine in mines:
        fig.add_trace(go.Bar(
            x=df.index,
            y=df[mine],
            name=mine
        ))
    fig.update_layout(
        title="Total Daily Output Stacked by Mine",
        xaxis_title="Date",
        yaxis_title="Output",
        barmode='stack',
        hovermode='x unified',
        height=450,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig
