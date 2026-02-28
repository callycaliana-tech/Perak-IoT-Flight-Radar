import streamlit as st
import pandas as pd
import folium
import os

# 1. Page Configuration
st.set_page_config(page_title="Perak IoT Flight Radar", layout="wide")
st.title("🛫 IoT Dashboard: Aircraft in Perak Airspace")
st.markdown("---")

FILE_NAME = "perak_flight_data.csv"

if os.path.exists(FILE_NAME):
    # Load and clean data
    df_raw = pd.read_csv(FILE_NAME)
    
    # Filter strictly for Perak coordinates
    df = df_raw[
        (df_raw['lat'] >= 3.6) & (df_raw['lat'] <= 6.0) & 
        (df_raw['long'] >= 100.0) & (df_raw['long'] <= 101.8)
    ].copy()

    if not df.empty:
        # --- PART 1: SYSTEM METRICS ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Data Points Captured", len(df))
        col2.metric("Unique ICAO24 Identified", df['icao24'].nunique())
        col3.metric("Last Sync Time", str(df['timestamp'].iloc[-1]))

        # --- PART 2: INTERACTIVE MAP ---
        st.subheader("📍 Live Map Visualization")
        m = folium.Map(location=[4.8, 101.0], zoom_start=8, tiles="CartoDB positron")
        
        # Plot latest position of each aircraft
        latest = df.sort_values('timestamp').groupby('icao24').last().reset_index()
        for _, row in latest.iterrows():
            folium.Marker(
                location=[float(row['lat']), float(row['long'])],
                popup=f"Callsign: {row['callsign']}<br>Origin: {row['origin']}",
                tooltip=f"Alt: {row['altitude']}m",
                icon=folium.Icon(color='red', icon='plane')
            ).add_to(m)

        st.components.v1.html(m._repr_html_(), height=500)

        # 💡 BONUS FEATURE: Saves a standalone file for your lecturer
        # They can right-click this file in the folder and "Open with Chrome"
        m.save("PERAK_RADAR_MAP.html")

        # --- PART 3: TABLE DATABASE ---
        st.markdown("---")
        st.subheader("📊 Database Logs (Perak Airspace Only)")
        
        # Displaying requested columns with newest data first
        cols = ['icao24', 'callsign', 'origin', 'long', 'lat', 'altitude', 'timestamp']
        st.dataframe(df[cols].sort_values(by='timestamp', ascending=False), use_container_width=True)
        
        # Download link for the CSV
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Database (.csv)", data=csv_data, file_name="perak_flight_logs.csv")
    
    else:
        st.warning("⚠️ Waiting for main.py to collect Perak data...")
else:
    st.error("❌ Database not found. Please run 'main.py' first to start capturing data.")