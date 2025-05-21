import streamlit as st
import pandas as pd
import numpy as np
import joblib
import pickle
from keras.models import load_model

def show_model_page():
   # st.set_page_config(page_title="Model-Based Anomaly Predictions", layout="wide")

    # -------------------- PAGE HEADER -------------------- #
    st.title("🤖 Model-Based Anomaly Predictions")
    st.write("This page is for engineers to interact with the anomaly detection model.")

    # -------------------- TAB LAYOUT -------------------- #
    tab1, = st.tabs(["📊 Model Predictions"])

    with tab1:
        # --- Utility Function ---
        def preprocess_and_predict(df, model_type):
            with open("scaler.pkl", "rb") as f:
                scaler = pickle.load(f)
            with open("pca.pkl", "rb") as f:
                pca = pickle.load(f)

            if model_type == "Autoencoder":
                model = load_model("autoencoder.keras")
                _, feature_cols = joblib.load("autoencoder_model.pkl")
            else:
                model = joblib.load("isolation_forest.pkl")
                _, feature_cols = joblib.load("isolation_model.pkl")

            X = df[feature_cols].copy()
            X = X.fillna(X.mean())
            X_scaled = scaler.transform(X)
            X_input = pca.transform(X_scaled) if model_type == "Isolation Forest" else X_scaled

            if model_type == "Isolation Forest":
                preds = model.predict(X_input)
                df['prediction'] = np.where(preds == -1, 'Anomaly', 'Normal')
                df['reconstruction_error'] = np.nan
            else:
                reconstructed = model.predict(X_input)
                mse = np.mean(np.square(X_input - reconstructed), axis=1)
                threshold = np.percentile(mse, 95)
                df['reconstruction_error'] = mse
                df['prediction'] = np.where(mse > threshold, 'Anomaly', 'Normal')

            return df

        # --- Load Data ---
        try:
            data = pd.read_csv("merged.csv")
            data['timestamp'] = pd.to_datetime(data['timestamp'])
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

        # --- Model Selection ---
        model_choice = st.selectbox("Choose a model", ["Isolation Forest", "Autoencoder"])

        # --- Run Prediction Button ---
        if st.button("🔍 Run Prediction"):
            results = preprocess_and_predict(data.copy(), model_type=model_choice)

            # --- Calculate Summary Metrics ---
            total_records = len(results)
            total_anomalies = (results['prediction'] == 'Anomaly').sum()
            total_sites = results['site_id'].nunique() if 'site_id' in results.columns else "N/A"
            affected_sites = results[results['prediction'] == 'Anomaly']['site_id'].nunique() if 'site_id' in results.columns else "N/A"

            # --- Display Summary Metrics ---
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🧾 Total Records", total_records)
            col2.metric("🚨 Total Anomalies", total_anomalies)
            col3.metric("📍 Total Sites", total_sites)
            col4.metric("⚠️ Affected Sites", affected_sites)

            # --- Display Anomalies ---
            anomalies = results[results['prediction'] == 'Anomaly']
            st.dataframe(anomalies, use_container_width=True)

            # --- Download Button ---
            csv = anomalies.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download Anomalies CSV", data=csv, file_name=f"{model_choice}_anomalies.csv")
        else:
            st.info("Click the button above to run model predictions.")
