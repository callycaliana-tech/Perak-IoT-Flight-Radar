import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
import os
import requests

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(page_title="Perak IoT Flight Radar", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    [data-testid="stMetric"] { background-color: #D1E9FF !important; border: 2px solid #3B82F6 !important; padding: 20px !important; border-radius: 10px !important; }
    h1, h2, h3, h4, label, p { color: black !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🛫 IoT Dashboard: Perak Airspace Radar")

FILE_NAME = "perak_flight_data.csv"

# ===============================
# WEATHER FETCH (CACHED)
# ===============================
@st.cache_data(ttl=300)
def fetch_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=wind_speed_10m,precipitation"
        res = requests.get(url, timeout=1.0)
        return res.json().get('current', {})
    except:
        return None

# ===============================
# LOAD CSV
# ===============================
if os.path.exists(FILE_NAME):
    try:
        df = pd.read_csv(FILE_NAME, encoding='utf-8', on_bad_lines='skip')  # skip bad lines

        # Standardize column names
        df.columns = [c.strip().lower() for c in df.columns]

        for col in ['lat', 'long', 'altitude', 'velocity']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df = df[
            (df['lat'] >= 3.6) & (df['lat'] <= 6.0) &
            (df['long'] >= 100.0) & (df['long'] <= 101.8)
        ].copy()

        if not df.empty:
            df['callsign'] = df['callsign'].fillna("UNKNOWN").astype(str).str.strip()
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

            # ===============================
            # LIVE STATISTICS
            # ===============================
            st.subheader("📊 Live Statistics")
            k1, k2, k3 = st.columns(3)
            k1.metric("Captured Data", len(df))
            k2.metric("Unique Aircraft", df['icao24'].nunique())
            k3.metric("Last Update", df['timestamp'].max().strftime('%H:%M:%S') if pd.notnull(df['timestamp'].max()) else "N/A")

            # ===============================
            # CONTROLS
            # ===============================
            with st.container(border=True):
                st.subheader("🔍 Main Radar Controls")
                cl, cr = st.columns([1, 1.5])

                with cl:
                    f_list = ["All Flights"] + sorted(df['callsign'].dropna().unique().tolist())
                    selected_flight = st.selectbox("SEARCH BY CALLSIGN:", f_list)

                with cr:
                    st.write("MAP DISPLAY OVERLAYS:")
                    p1, p2 = st.columns(2)
                    enable_weather = p1.checkbox("Enable Weather Risk (Green/Yellow)", value=False)
                    enable_heatmap = p2.checkbox("Enable Traffic Heatmap (Glow)", value=True)

                cs1, cs2 = st.columns(2)
                selected_alt = cs1.slider("ALTITUDE (m):", 0, 15000, (0, 15000))
                selected_vel = cs2.slider("VELOCITY (m/s):", 0, 500, (0, 500))

            # ===============================
            # FILTER DATA
            # ===============================
            display_df = df.copy().sort_values(by='timestamp', ascending=False)

            if selected_flight != "All Flights":
                display_df = display_df[display_df['callsign'].str.strip() == selected_flight]

            display_df = display_df[
                (display_df['altitude'] >= selected_alt[0]) &
                (display_df['altitude'] <= selected_alt[1])
            ]

            # ===============================
            # MAP
            # ===============================
            st.subheader(f"📍 Radar View: {selected_flight}")
            m = folium.Map(location=[4.8, 101.0], zoom_start=9, tiles="OpenStreetMap")

            # -------------------------------
            # TRAFFIC GLOW (ZONE BASED) ONLY IF HEATMAP
            # -------------------------------
            if enable_heatmap and not display_df.empty:
                zone_df = display_df.copy()
                zone_df["zone_lat"] = zone_df["lat"].round(1)
                zone_df["zone_lon"] = zone_df["long"].round(1)
                zone_counts = zone_df.groupby(["zone_lat", "zone_lon"]).size().reset_index(name="count")

                for _, row in zone_counts.iterrows():
                    lat = row["zone_lat"]
                    lon = row["zone_lon"]
                    count = row["count"]

                    if count >= 15:
                        color = "red"
                        opacity = 0.6
                    elif count >= 8:
                        color = "orange"
                        opacity = 0.4
                    else:
                        color = "yellow"
                        opacity = 0.2

                    folium.Circle(
                        location=[lat, lon],
                        radius=15000,
                        color=None,
                        fill=True,
                        fill_color=color,
                        fill_opacity=opacity
                    ).add_to(m)

                # Heatmap
                heat_data = [[row['lat'], row['long']] for _, row in display_df.iterrows()]
                HeatMap(heat_data, radius=20, blur=15, min_opacity=0.4).add_to(m)

            # -------------------------------
            # AIRCRAFT MARKERS (WEATHER RISK)
            # -------------------------------
            risk_list = []
            weather_cache = {}

            # Always show all flights for weather risk
            marker_df = display_df.copy() if selected_flight == "All Flights" else display_df.head(100)

            with st.spinner("Processing Radar & Weather Data..."):
                for _, row in marker_df.iterrows():
                    marker_color = "blue"
                    status = "Normal"

                    if enable_weather:
                        latlon = (round(row['lat'], 2), round(row['long'], 2))
                        if latlon not in weather_cache:
                            weather_cache[latlon] = fetch_weather(*latlon)
                        w = weather_cache[latlon]
                        wind = w.get('wind_speed_10m', 0) if w else 0
                        rain = w.get('precipitation', 0) if w else 0

                        if wind > 8 or rain > 0:
                            marker_color = "orange"
                            status = "Caution"
                        else:
                            marker_color = "green"
                            status = "Safe"

                        risk_list.append({
                            "Callsign": row['callsign'],
                            "Wind Speed (km/h)": wind,
                            "Status": status
                        })

                    folium.CircleMarker(
                        location=[float(row['lat']), float(row['long'])],
                        radius=6,
                        color=marker_color,
                        fill=True,
                        fill_opacity=0.8,
                        popup=f"Flight: {row['callsign']} | Status: {status}"
                    ).add_to(m)

            # -------------------------------
            # MAP DISPLAY
            # -------------------------------
            st.components.v1.html(m._repr_html_(), height=600)

            # ===============================
            # ALTITUDE GRAPH + DATA TABLE (EXPANDER)
            # ===============================
            with st.expander("📈 Altitude Profile & Data History Logs"):
                if not display_df.empty:
                    chart_df = display_df.sort_values('timestamp')
                    if selected_flight == "All Flights":
                        pivot_df = chart_df.pivot_table(index='timestamp', columns='callsign', values='altitude')
                        st.line_chart(pivot_df)
                    else:
                        st.line_chart(chart_df.set_index('timestamp')['altitude'])
                else:
                    st.info("No data available for the graph.")

                if enable_weather and risk_list:
                    st.subheader("📊 Top Aircraft by Weather Risk")
                    risk_df = pd.DataFrame(risk_list)
                    st.dataframe(risk_df.head(20), use_container_width=True)

                st.subheader("📋 Data History Logs")
                csv_download = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Filtered Data (CSV)",
                    data=csv_download,
                    file_name=f"perak_radar_export_{selected_flight}.csv",
                    mime="text/csv",
                )
                st.dataframe(display_df.head(50), use_container_width=True)

    except Exception as e:
        st.error(f"Technical error: {e}")
else:
    st.error("CSV file not found.")
