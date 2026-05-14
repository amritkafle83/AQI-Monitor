import requests
import pandas as pd
from datetime import datetime
import os
import time
import sqlite3
import logging

# --- Setup Logging Configuration ---
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    filename='logs/system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

API_KEY = "b2d346bcd961788c78fc585b7d518c96"
LAT = "27.7172"
LON = "85.3240"

def get_complete_data():
    pollution_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={LAT}&lon={LON}&appid={API_KEY}"
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"
    
    try:
        p_res = requests.get(pollution_url, timeout=10)
        p_res.raise_for_status()
        w_res = requests.get(weather_url, timeout=10)
        w_res.raise_for_status()
        
        p_json = p_res.json()
        w_json = w_res.json()
        
        data = {
            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'PM2.5': p_json['list'][0]['components']['pm2_5'],
            'PM10': p_json['list'][0]['components']['pm10'],
            'Temp': w_json['main']['temp'],
            'Humidity': w_json['main']['humidity']
        }
        logging.info("Data successfully fetched from API.")
        return data
    except Exception as e:
        logging.error(f"API Fetch Error: {e}")
        print(f"Error: {e}")
        return None

def save_to_db(data):
    try:
        conn = sqlite3.connect('data/pollution_system.db')
        cursor = conn.cursor()
        query = '''INSERT INTO measurements (timestamp, pm25, pm10, temp, humidity) 
                   VALUES (?, ?, ?, ?, ?)'''
        values = (data['Timestamp'], data['PM2.5'], data['PM10'], data['Temp'], data['Humidity'])
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        logging.info("SQL Success: Measurements stored.")
    except Exception as e:
        logging.error(f"Database Storage Error: {e}")

if __name__ == "__main__":
    logging.info("System Startup Initiated.")
    print("--- System Running (Check logs/system.log for details) ---")
    
    while True:
        combined_data = get_complete_data()
        if combined_data:
            save_to_db(combined_data)
        
        time.sleep(900)