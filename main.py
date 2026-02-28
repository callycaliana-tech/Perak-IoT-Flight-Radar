import requests  
import pandas as pd
import time
from datetime import datetime
import os

# GPS Bounding Box for Perak, Malaysia
# This ensures you only get planes over the state of Perak
params = {
    'lamin': 3.6, 
    'lomin': 100.0, 
    'lamax': 6.0, 
    'lomax': 101.8
}

FILE_NAME = "perak_flight_data.csv"

def fetch_and_save():
    url = "https://opensky-network.org/api/states/all"
    try:
        # Requesting data from OpenSky API
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data['states']:
                # Columns: ICAO24, Callsign, Country, Time, LastContact, Long, Lat, BaroAltitude
                raw_data = [s[:8] for s in data['states']]
                df = pd.DataFrame(raw_data, columns=['icao24', 'callsign', 'origin', 'time_pos', 'last_con', 'long', 'lat', 'altitude'])
                
                # Add a readable timestamp for your database
                df['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Save/Append to CSV (This acts as your Database)
                # 'a' means append, so it doesn't delete previous data
                file_exists = os.path.isfile(FILE_NAME)
                df.to_csv(FILE_NAME, mode='a', index=False, header=not file_exists)
                
                print(f"[{df['timestamp'].iloc[0]}] Successfully saved {len(df)} aircraft in Perak.")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No aircraft detected in Perak right now.")
        else:
            print(f"API Error: {response.status_code}")
            
    except Exception as e:
        print(f"Connection Error: {e}. Retrying in 2 mins...")

# --- MAIN LOOP ---
print("--- TFB2093 IoT DATA ACQUISITION SYSTEM ---")
print("Status: Started")
print(f"Saving to: {os.path.abspath(FILE_NAME)}")
print("Goal: 3 Continuous Days of Collection")
print("Action: Keep this window open and your laptop connected to internet.")
print("-------------------------------------------")

while True:
    fetch_and_save()
    # Wait 120 seconds (2 minutes) to stay within free API limits
    time.sleep(120)