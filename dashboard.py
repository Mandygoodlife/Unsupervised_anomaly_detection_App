# dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import os
import csv
import sendgrid
from sendgrid.helpers.mail import Mail

def send_email_alert(subject, content):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=st.secrets["sendgrid"]["api_key"])
        from_email = st.secrets["sendgrid"]["sender_email"]
        to_email = st.secrets["sendgrid"]["recipient_email"]

        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=content
        )
        response = sg.send(message)

        if response.status_code == 202:
            st.success("✅ Email alert sent successfully.")
        else:
            st.error(f"❌ Failed to send email. Status code: {response.status_code}")

    except Exception as e:
        st.error(f"❌ Error sending email: {str(e)}")

def log_email(subject, content, site_count):
    log_file = "email_logs.csv"
    log_exists = os.path.exists(log_file)

    with open(log_file, mode="a", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        if not log_exists:
            writer.writerow(["Timestamp", "Subject", "Affected Sites Count", "Message"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), subject, site_count, content])

def show_dashboard():
    st.title("📊 Network Anomaly Detection Dashboard")

    # Load data
    main_data = pd.read_csv("data.csv")
    main_data['timestamp'] = pd.to_datetime(main_data['timestamp'])

    non_kpi_columns = ['timestamp', 'site_id']
    kpi_columns = [col for col in main_data.columns if col not in non_kpi_columns]

    # Generate severity if missing
    if 'severity' not in main_data.columns:
        selected_kpi = kpi_columns[0] if kpi_columns else None
        if selected_kpi:
            threshold = main_data[selected_kpi].quantile(0.95)
            main_data['severity'] = np.where(main_data[selected_kpi] > threshold, 'anomaly', 'normal')
        else:
            main_data['severity'] = 'normal'

    # Severity class
    if kpi_columns:
        main_kpi = kpi_columns[0]
        q80 = main_data[main_kpi].quantile(0.80)
        q90 = main_data[main_kpi].quantile(0.90)
        q95 = main_data[main_kpi].quantile(0.95)

        def classify_severity(val):
            if val > q95:
                return 'Critical'
            elif val > q90:
                return 'High'
            elif val > q80:
                return 'Moderate'
            else:
                return 'Minor'

        main_data['severity_class'] = main_data[main_kpi].apply(classify_severity)
    else:
        main_data['severity_class'] = 'Minor'

    # Sidebar upload
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 Upload Your Own CSV")
    user_file = st.sidebar.file_uploader("Upload a CSV file", type=["csv"])
    if user_file is not None:
        user_data = pd.read_csv(user_file)
        st.subheader("📄 Custom File Preview")
        st.write(user_data.head())
        st.bar_chart(user_data.select_dtypes(include=np.number))

    # Filters
    st.sidebar.header("🔍 Filter Options")
    sites = main_data['site_id'].unique()
    selected_site = st.sidebar.selectbox("Select Site", options=np.append(["All"], sites))
    selected_kpi = st.sidebar.selectbox("Select KPI", options=kpi_columns)
    selected_range = st.sidebar.date_input("Select Time Range", value=(main_data['timestamp'].min(), main_data['timestamp'].max()))
    selected_severity = st.sidebar.multiselect("Select Severity Class", options=['Minor', 'Moderate', 'Critical'], default=['Minor', 'Moderate', 'Critical'])

    # Filtering
    filtered_data = main_data.copy()
    if selected_site != "All":
        filtered_data = filtered_data[filtered_data['site_id'] == selected_site]
    filtered_data = filtered_data[(filtered_data['timestamp'] >= pd.to_datetime(selected_range[0])) &
                                  (filtered_data['timestamp'] <= pd.to_datetime(selected_range[1]))]
    filtered_data = filtered_data[filtered_data['severity_class'].isin(selected_severity)]

    # Tabs
    tab1, tab2 = st.tabs(["📈 Overview", "🔔 Alerts & Trends"])

    with tab1:
        st.subheader("📊 Metrics Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Records", len(filtered_data))
        col2.metric("Total Anomalies", filtered_data[filtered_data['severity'] != 'normal'].shape[0])
        col3.metric("Total Sites", main_data['site_id'].nunique())
        col4.metric("Affected Sites", filtered_data[filtered_data['severity'] != 'normal']['site_id'].nunique())

        st.subheader(f"{selected_kpi} Over Time")
        if not filtered_data.empty:
            fig = px.line(filtered_data, x='timestamp', y=selected_kpi, color='site_id', title=f'{selected_kpi} Timeline')
            anomalies = filtered_data[filtered_data['severity'] != 'normal']
            if not anomalies.empty:
                fig.add_scatter(x=anomalies['timestamp'], y=anomalies[selected_kpi], mode='markers',
                                marker=dict(color='red', size=8, symbol='x'), name='Anomalies')
            filtered_data['rolling_avg'] = filtered_data[selected_kpi].rolling(window=10, min_periods=1).mean()
            fig.add_scatter(x=filtered_data['timestamp'], y=filtered_data['rolling_avg'],
                            mode='lines', line=dict(dash='dot', color='orange'), name='Moving Average')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data for selected filters.")

    with tab2:
        st.subheader("🔔 Alert Summary")
        summary_counts = filtered_data[filtered_data['severity'] != 'normal']['severity_class'].value_counts()
        for level in ['Critical', 'Moderate', 'Minor']:
            count = summary_counts.get(level, 0)
            st.write(f"**{level} Alerts:** {count}")

        st.subheader("📅 Anomaly Trend")
        trend_option = st.selectbox("Granularity", ["Weekly", "Monthly", "Yearly"])
        if not filtered_data.empty:
            trend_data = filtered_data.copy()
            trend_data['period'] = trend_data['timestamp'].dt.to_period({'Weekly': 'W', 'Monthly': 'M', 'Yearly': 'Y'}[trend_option]).astype(str)
            trend_group = trend_data[trend_data['severity'] != 'normal'].groupby('period').size().reset_index(name='anomaly_count')
            fig = px.bar(trend_group, x='period', y='anomaly_count', color_discrete_sequence=['red'])
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("📬 Email Alerts")
        affected_sites = filtered_data[filtered_data['severity'] != 'normal']['site_id'].unique()
        site_count = len(affected_sites)
        site_list_str = ', '.join(map(str, affected_sites))

        if st.button("Send Test Alert"):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if site_count > 0:
                message = (f"🚨 Critical anomaly detected!\n\n🕒 {current_time}\n"
                           f"⚠️ Affected Sites ({site_count}): {site_list_str}")
            else:
                message = f"✅ No critical anomalies as of {current_time}."

            subject = "🚨 Critical Anomaly Detected" if site_count > 0 else "✅ No Anomalies Detected"
            send_email_alert(subject, message)
            log_email(subject, message, site_count)

        if os.path.exists("email_logs.csv"):
            logs = pd.read_csv("email_logs.csv")
            st.dataframe(logs, use_container_width=True)
        else:
            st.info("No email logs yet.")
