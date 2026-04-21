# How to use

This project is closely tied to a self made Google spreadhseets generator of fake data that has multiple configurable options like mean, deviation, corellation, specifying anomaly events (spikes or dips) etc.

Run and deploy the project from your machine or you can access the publicly available option here:

**link**

### You can:
- see tabs for total and each mine individually, with statistics and anomaly detection
- select which type of graph you want to see (Stacked is swapped to Bar graph for singular mine tabs)
- switch trendline on/off and choose wich degree trendline it will be
- toggle such anomaly detection algorthims as : IQR rule, Z-score, Moving Average and Grubbs test
- choose parameters for each anomaly detection algorithm
- see a table of events marked as anomalies for each tab (single mine or total)
- generate and download PDF report of findings with graphs you chose and tables for each mine's anomaly events

**Note**: as data generation is accessed via public Google Spreadsheets link, and only possible way there to get a random value fast is the usage of RAND() function (meaning each page refresh or download creates new values) -> **I additionally provided a debug switch to toggle viewing of raw data table that you've fetched from the generator**

# How to run

```
pip install -r requirements.txt
```
```
streamlit run app.py
```

This will either: 
- directly open your browser to a localhost link of deployed streamlit app
- give you a link, which usually is: http://localhost:8501