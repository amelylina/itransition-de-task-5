import pandas as pd
import plotly.graph_objects as go

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
