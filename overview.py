import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px


st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select a Page", ["Overview", "Anomaly Viewer", "Alerts & Logs", "Reports", "Settings"])

merged_data = pd.read_csv("merged.csv")

selected_site = st.sidebar.selectbox("Select Site", merged_data['site_id'].unique())
selected_kpi = st.sidebar.multiselect("Select KPI(s)", ['packet_loss', 'latency', 'throughput'])
date_range = st.sidebar.date_input("Select Date Range", [merged_data['timestamp'].min(), merged_data['timestamp'].max()])
severity_filter = st.sidebar.selectbox("Select Severity", ["All", "Minor", "Moderate", "Critical"])


def show_overview():
    st.title("📊 Network Overview")
    st.write("Welcome to the anomaly detection dashboard!")
    st.markdown("""
    This section gives a high-level summary of:
    - Network health
    - KPI trends
    - Recent anomalies
    """)
    # Example dummy chart
    st.line_chart([10, 20, 15, 30, 25])


if page == "Overview":
    show_overview()
elif page == "Anomaly Viewer":
    st.write("Overview section is under construction.")
elif page == "Alerts & Logs":
    st.write("Overview section is under construction.")

elif page == "Reports":
    st.write("Overview section is under construction.")

elif page == "Settings":
    st.write("Overview section is under construction.")


def show_overview():
    st.title("Network Health Overview")
    # line plots, pie charts, etc.

def show_anomaly_viewer():
    st.title("Anomaly Detection Viewer")
    # plot time series with anomalies

def show_alerts_logs():
    st.title("Anomaly Alerts and Logs")
    # show data table, export, and email button

def show_reports():
    st.title("Generate Report")
    # display filters and download buttons

def show_settings():
    st.title("Settings")
    # Email, thresholds, model upload


#st.pyplot(fig)  # or st.plotly_chart()
st.write("Overview section is under construction.")
