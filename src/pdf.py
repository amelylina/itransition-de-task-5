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
from src.config import AnomalyParams, BRAND_ACCENT, BRAND_DARK, ROW_ALT
from src.stats import compute_stats, group_anomalies
from src.charts import build_chart, build_stacked_chart
from src.ui import compute_all_anomalies

_BASE_TABLE_STYLE = [
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BRAND_ACCENT)),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('GRID', (0, 0), (-1, -1), 0.6, colors.grey),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor(ROW_ALT)]),
]

def _figure_to_png_bytes(fig, width=1100, height=450)-> bytes:
    try:
        return fig.to_image(format="png", width=width, height=height, scale=2)
    except Exception as e:
        raise RuntimeError(
            f"Chart export failed ({e})"
        ) from e

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
    t.setStyle(TableStyle(_BASE_TABLE_STYLE+[('ALIGN', (1, 0), (1, -1), 'RIGHT')]))
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
            row.append("●" if mask.loc[d] else "")
        rows.append(row)
    
    col_widths = [3*cm, 2.5*cm] + [3*cm] * len(anomalies)
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(_BASE_TABLE_STYLE+[
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    return t

def _settings_table(anomaly_params: AnomalyParams) -> Table | Paragraph:
    rows = [["Test", "Status", "Parameters"]]
    
    if anomaly_params.iqr_enabled:
        rows.append(["IQR rule", "Enabled", f"k = {anomaly_params.iqr_k}"])
    if anomaly_params.zscore_enabled:
        rows.append(["Z-score", "Enabled", f"threshold = {anomaly_params.zscore_threshold}σ"])
    if anomaly_params.ma_enabled:
        rows.append([
            "Moving average",
            "Enabled",
            f"window = {anomaly_params.ma_window} days, threshold = {anomaly_params.ma_threshold}%",
        ])
    if anomaly_params.grubbs_enabled:
        rows.append(["Grubbs' test", "Enabled", f"α = {anomaly_params.grubbs_alpha}"])
    
    if len(rows) == 1:
        return Paragraph("No anomaly detection tests were enabled.", getSampleStyleSheet()['Italic'])
    
    t = Table(rows, colWidths=[4*cm, 2.5*cm, 8*cm])
    t.setStyle(TableStyle(_BASE_TABLE_STYLE+[('ALIGN', (1, 0), (1, -1), 'RIGHT')]))
    return t

def _page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(
        A4[0] - 2*cm, 1*cm,
        f"Page {doc.page}"
    )
    canvas.drawString(
        2*cm, 1*cm,
        "Weyland-Yutani Mining Operations Report"
    )
    canvas.restoreState()

def generate_pdf(
    df: pd.DataFrame,
    mines: list[str],
    chart_type: str,
    trendline_degree: int | None,
    anomaly_params: AnomalyParams,
) -> bytes:
    
    tab_names = ["Total"] + mines
    precomputed = {
        name: {
            'series': df[name],
            'stats': compute_stats(df[name]),
            'anomalies': compute_all_anomalies(df[name], anomaly_params),
        }
        for name in tab_names
    }
    
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=2*cm,
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title', parent=styles['Title'],
        fontSize=24, textColor=colors.HexColor(BRAND_DARK),
        spaceAfter=20,
    )
    h2_style = ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontSize=16, textColor=colors.HexColor(BRAND_DARK),
        spaceAfter=10,
    )
    h3_style = ParagraphStyle(
        'H3', parent=styles['Heading3'],
        fontSize=13, textColor=colors.HexColor(BRAND_DARK),
        spaceAfter=8,
    )
    body_style = styles['BodyText']
    
    story = []
    
    story.append(Paragraph("Weyland-Yutani Corporation", title_style))
    story.append(Paragraph("Mining Operations Analytics Report", h2_style))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now():%Y-%m-%d %H:%M}", body_style))
    story.append(Paragraph(f"<b>Date range:</b> {df.index.min()} to {df.index.max()}", body_style))
    story.append(Paragraph(f"<b>Mines covered:</b> {len(mines)} ({', '.join(mines)})", body_style))
    story.append(Paragraph(f"<b>Days of data:</b> {len(df)}", body_style))
    story.append(PageBreak())

    story.append(Paragraph("Contents", h2_style))
    toc_items = ["Methodology"] + [f"{name} — Statistics & Chart" for name in tab_names] + ["Anomaly Details"]
    for item in toc_items:
        story.append(Paragraph(f"• {item}", body_style))
    story.append(PageBreak())

    story.append(Paragraph("Methodology", h2_style))
    story.append(Paragraph(
        "This report summarizes daily mine output, descriptive statistics, "
        "and anomaly detection results across the following tests:",
        body_style,
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(_settings_table(anomaly_params))
    story.append(PageBreak())

    for name, data in precomputed.items():
        series = data['series']
        anomalies = data['anomalies']
        
        story.append(Paragraph(name, h2_style))
        story.append(_stats_table(series))
        story.append(Spacer(1, 0.5*cm))
        
        if chart_type == "Stacked" and name == "Total":
            fig = build_stacked_chart(df, mines,trendline_degree)
        else:
            effective_chart_type = "Bar" if chart_type == "Stacked" else chart_type
            fig = build_chart(name, series, effective_chart_type, anomalies, trendline_degree)
        
        img_bytes = _figure_to_png_bytes(fig)
        img_w_cm = 16
        img_h_cm = img_w_cm * (450 / 1100)
        story.append(Image(io.BytesIO(img_bytes), width=img_w_cm*cm, height=img_h_cm*cm))
        story.append(Spacer(1, 0.3*cm))
        
        story.append(Paragraph("Detected anomalies", h3_style))
        story.append(Spacer(1, 0.3*cm))
        story.append(_anomaly_table_flowable(series, anomalies))
        story.append(PageBreak())
    
    story.append(Paragraph("Anomaly Details", h2_style))
    any_anomaly_found = False
    for name, data in precomputed.items():
        series = data['series']
        anomalies = data['anomalies']
        any_flagged = pd.Series(False, index=series.index)
        for mask in anomalies.values():
            any_flagged = any_flagged | mask
        events = group_anomalies(any_flagged)
        if not events:
            continue
        
        story.append(Paragraph(name, h3_style))
        for start, end in events:
            any_anomaly_found = True
            event_slice = series.loc[start:end]
            peak_date = event_slice.idxmax() if event_slice.mean() > series.mean() else event_slice.idxmin()
            peak_value = series.loc[peak_date]
            mean= data['stats']['mean']
            std = data['stats']['std']
            sigma_dev = (peak_value - mean) / std if std > 0 else 0
            direction = "spike" if peak_value > mean else "drop"
            duration = (end - start).days + 1
            
            tests_fired = sorted({
                test for test, m in anomalies.items()
                if m.loc[start:end].any()
            })
            
            header_text = f"{start} to {end}" if start != end else f"{start}"
            story.append(Paragraph(header_text, body_style))
            story.append(Paragraph(
                f"Duration: {duration} day(s) &nbsp;&nbsp; "
                f"Type: {direction} &nbsp;&nbsp; "
                f"Peak: {peak_value:.2f} on {peak_date} ({sigma_dev:+.2f}σ) &nbsp;&nbsp; "
                f"Flagged by: {', '.join(tests_fired)}",
                body_style,
            ))
            story.append(Spacer(1, 0.3*cm))
        story.append(Spacer(1, 0.5*cm))
    
    if not any_anomaly_found:
        story.append(Paragraph("No anomalies detected across any tests.", body_style))
    
    doc.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    buf.seek(0)
    return buf.getvalue()