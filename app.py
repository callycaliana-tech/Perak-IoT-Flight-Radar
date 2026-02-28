import streamlit as st
import pandas as pd
import folium
import os  # <--- THIS WAS MISSING AND CAUSED YOUR ERROR

# 1. Page Configuration
st.set_page_config(page_title="Perak IoT Flight Radar", layout="wide")
st.title("🛫 IoT Dashboard: Aircraft in Perak Airspace")
st.markdown("---")

FILE_NAME = "perak_flight_data.csv"

# 9. This is where your error was: os.path.exists
if os.path.exists(FILE_NAME):
    # Load the Raw Database
    df_raw = pd.read_csv(FILE_NAME)
    
    # --- DATA PROCESSING: PERAK GEOFENCING ---
    # Filter strictly for Perak coordinates
    df_perak = df_raw[
        (df_raw['lat'] >= 3.6) & (df_raw['lat'] <= 6.0) & 
        (df_raw['long'] >= 100.0) & (df_raw['long'] <= 101.8)
    ].copy()

    if not df_perak.empty:
        # --- PART 1: STATS ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Records in Perak", len(df_perak))
        col2.metric("Unique Planes", df_perak['icao24'].nunique())
        col3.metric("Last Data Sync", str(df_perak['timestamp'].iloc[-1]))

        # --- PART 2: THE MAP ---
        st.subheader("📍 Live Map Visualization")
        m = folium.Map(location=[4.8, 101.0], zoom_start=8, tiles="CartoDB positron")
        
        latest = df_perak.sort_values('timestamp').groupby('icao24').last().reset_index()
        for _, row in latest.iterrows():
            folium.Marker(
                location=[float(row['lat']), float(row['long'])],
                popup=f"Callsign: {row['callsign']}",
                icon=folium.Icon(color='red', icon='plane')
            ).add_to(m)
        st.components.v1.html(m._repr_html_(), height=500)

        # --- PART 3: THE DATABASE TABLE ---
        st.markdown("---")
        st.subheader("📊 Database Logs (Perak Airspace)")
        
        # This displays the columns exactly in the order you requested
        display_columns = ['icao24', 'callsign', 'origin', 'time_pos', 'last_con', 'long', 'lat', 'altitude', 'timestamp']
        
        # Show the table on the website
        st.dataframe(df_perak[display_columns].sort_values(by='timestamp', ascending=False), use_container_width=True)
        
        # Download button for your report proof
        csv_data = df_perak[display_columns].to_csv(index=False).encode('utf-8')
        st.download_button("Download Perak Logs (CSV)", data=csv_data, file_name="perak_flight_logs.csv")
    
    else:
        st.warning("⚠️ No aircraft currently detected within Perak coordinates.")
else:
    st.error("Database file 'perak_flight_data.csv' not found! Make sure main.py is running.")