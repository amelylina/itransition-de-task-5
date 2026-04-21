import io
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image,
)
from src.config import AnomalyParams
from src.stats import compute_stats
from src.charts import build_chart, build_stacked_chart
from src.ui import compute_all_anomalies

def _figure_to_png_bytes(fig, width=1100, height=450)-> bytes:
    return fig.to_image(format="png", width=width, height=height,scale=2)

def _stats_table(series: pd.Series):
    s = compute_stats(series)
    data = [
        ["Metric", "Value"],
        ["Mean", f"{s['mean']:.2f}"],
        ["Median", f"{s['median']:.2f}"],
        ["Std Dev", f"{s['std']:.2f}"],
        ["IQR", f"{s['iqr']:.2f}"],
        ["Q1", f"{s['q1']:.2f}"],
        ["Q3", f"{s['q3']:.2f}"],
    ]
    t = Table(data, colWidths=[4*cm, 4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#536474")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    return t

def _anomaly_table_flowable(series: pd.Series, anomalies: dict[str, pd.Series]) -> Table | Paragraph:
    any_flagged = pd.Series(False, index=series.index)
    for mask in anomalies.values():
        any_flagged = any_flagged | mask
    
    if not any_flagged.any():
        return Paragraph("No anomalies detected.", getSampleStyleSheet()['Italic'])
    
    header = ["Date", "Value"] + list(anomalies.keys())
    rows = [header]
    for d in series.index[any_flagged]:
        row = [str(d), f"{series.loc[d]:.2f}"]
        for test_name, mask in anomalies.items():
            row.append("✓" if mask.loc[d] else "")
        rows.append(row)
    
    col_widths = [3*cm, 2.5*cm] + [2*cm] * len(anomalies)
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#536474')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    return t

def generate_pdf(
    df: pd.DataFrame,
    mines: list[str],
    chart_type: str,
    trendline_degree: int | None,
    anomaly_params: AnomalyParams,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=2*cm,
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title', parent=styles['Title'],
        fontSize=24, textColor=colors.HexColor('#2c3e50'),
        spaceAfter=20,
    )
    h2_style = ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontSize=16, textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
    )
    body_style = styles['BodyText']
    
    story = []
    
    story.append(Paragraph("Weyland-Yutani Corporation", title_style))
    story.append(Paragraph("Mining Operations Analytics Report", h2_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
    story.append(Paragraph(f"<b>Date range:</b> {df.index.min()} to {df.index.max()}", body_style))
    story.append(Paragraph(f"<b>Mines:</b> {', '.join(mines)}", body_style))
    story.append(Paragraph(f"<b>Days of data:</b> {len(df)}", body_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"<b>Anomaly detection settings:</b>", body_style))
    
    story.append(PageBreak())
    
    tab_names = ["Total"] + mines
    for name in tab_names:
        series = df[name]
        anomalies = compute_all_anomalies(series, anomaly_params)
        
        story.append(Paragraph(name, h2_style))
        story.append(_stats_table(series))
        story.append(Spacer(1, 0.5*cm))
        
        if chart_type == "Stacked" and name == "Total":
            fig = build_stacked_chart(df, mines)
        else:
            effective_chart_type = "Bar" if chart_type == "Stacked" else chart_type
            fig = build_chart(name, series, effective_chart_type, anomalies, trendline_degree)
        
        img_bytes = _figure_to_png_bytes(fig)
        story.append(Image(io.BytesIO(img_bytes), width=16*cm, height=6.5*cm))
        story.append(Spacer(1, 0.3*cm))
        
        story.append(Paragraph("<b>Detected anomalies</b>", body_style))
        story.append(_anomaly_table_flowable(series, anomalies))
        story.append(PageBreak())
    
    story.append(Paragraph("Anomaly Details", h2_style))
    any_anomaly_found = False
    for name in tab_names:
        series = df[name]
        anomalies = compute_all_anomalies(series, anomaly_params)
        any_flagged = pd.Series(False, index=series.index)
        for mask in anomalies.values():
            any_flagged = any_flagged | mask
        
        for d in series.index[any_flagged]:
            any_anomaly_found = True
            tests_that_flagged = [t for t, m in anomalies.items() if m.loc[d]]
            mean = series.mean()
            value = series.loc[d]
            deviation_pct = ((value - mean) / mean) * 100
            direction = "spike" if value > mean else "drop"
            
            story.append(Paragraph(f"<b>{name} — {d}</b>", body_style))
            story.append(Paragraph(
                f"Value: {value:.2f} &nbsp;&nbsp; "
                f"Type: {direction} &nbsp;&nbsp; "
                f"Deviation from mean: {deviation_pct:+.1f}%",
                body_style,
            ))
            story.append(Paragraph(
                f"Flagged by: {', '.join(tests_that_flagged)}",
                body_style,
            ))
            story.append(Spacer(1, 0.3*cm))
    
    if not any_anomaly_found:
        story.append(Paragraph("No anomalies detected across any tests.", body_style))
    
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()