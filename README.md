# Weyland-Yutani mining operations dashboard
A Streamlit dashboard that analyzes daily mining output data, detects anomalies using multiple statistical tests, and generates detailed PDF reports.

Built as part of a data engineering internship task.
# How to use

This project is closely tied to a self made Google spreadsheets generator of fake data that has multiple configurable options like mean, deviation, corelation, specifying anomaly events (spikes or dips) etc.

Run and deploy the project from your machine or you can access the publicly available option here:

**link**

## You can:
- see tabs for total and each mine individually, with statistics and anomaly detection
- select which type of graph you want to see (Stacked is swapped to Bar graph for singular mine tabs)
- switch trendline on/off and choose which degree trendline it will be
- toggle anomaly detection algorithms like: 
    - IQR rule
    - Z-score
    - Moving Average 
    - Grubbs test
- choose parameters for each anomaly detection algorithm
- see a table of events marked as anomalies for each tab (single mine or total)
- generate and download PDF report of findings with graphs you chose and tables for each mine's anomaly events

**Note**: as data generation is accessed via public Google Spreadsheets link, and only possible way there to get a random value fast is the usage of RAND() function (meaning each page refresh or download creates new values) -> **I additionally provided a debug switch to toggle viewing of raw data table that you've fetched from the generator**

# How to run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will open http://localhost:8501 in your browser automatically. If it doesn't, visit that URL manually.