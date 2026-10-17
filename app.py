import os
from datetime import datetime
import requests
from flask import Flask, jsonify, render_template_string


app = Flask(__name__)


# CONFIGURATION
API_KEY = os.environ.get("ELECTRICITY_MAPS_API_KEY", "em_dvZWWhYbyesH4J3FAgcbu5gpExFgxwT5")
ZONE = os.environ.get("ELECTRICITY_ZONE", "CA-ON")


# Coordinates for Ontario (Toronto region) used for Open-Meteo free weather check
LAT = 43.65
LON = -79.38




def fetch_open_meteo_green_window():
   """Fetches free hourly solar radiation and wind forecasts from Open-Meteo to find clean windows."""
   try:
       url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=shortwave_radiation,wind_speed_10m&timezone=auto"
       response = requests.get(url, timeout=10)
       if response.status_code == 200:
           data = response.json()
           hourly = data.get("hourly", {})
           times = hourly.get("time", [])
           solar = hourly.get("shortwave_radiation", [])
           wind = hourly.get("wind_speed_10m", [])


           green_blocks = []
           current_block = None


           for i, time_str in enumerate(times):
               s_val = solar[i] if i < len(solar) else 0
               w_val = wind[i] if i < len(wind) else 0


               # Define "clean window" criteria: High sun (>350 W/m²) OR high wind (>20 km/h)
               if (s_val is not None and s_val > 350) or (w_val is not None and w_val > 20):
                   dt = datetime.fromisoformat(time_str)
                   formatted_time = dt.strftime("%I:%M %p").lstrip("0")


                   if not current_block:
                       current_block = {"start": formatted_time, "end": formatted_time}
                   else:
                       current_block["end"] = formatted_time
               else:
                   if current_block:
                       green_blocks.append(current_block)
                       current_block = None


           if current_block:
               green_blocks.append(current_block)


           if green_blocks:
               window = green_blocks[0]
               if window["start"] == window["end"]:
                   return f"Next clean window (Solar/Wind surge): ~{window['start']}"
               else:
                   return f"Next clean window (Solar/Wind surge): {window['start']} – {window['end']}"
           else:
               return "No high solar/wind generation windows predicted soon."
   except Exception as e:
       print(f"Error fetching Open-Meteo: {e}")


   return "Weather-based forecast unavailable."




def fetch_carbon_intensity():
   """Fetches real-time carbon intensity, clean energy percentage, and free weather-based green windows."""
   if API_KEY == "YOUR_API_KEY_HERE":
       return {
           "zone": ZONE,
           "carbonIntensity": 142,
           "renewablePercentage": 82.5,
           "forecastMessage": "Next clean window (Solar/Wind surge): 12:00 PM – 4:00 PM",
           "status": "green",
           "message": "Eco-Friendly Window Open: Great time to run laundry, vacuum, or charge devices."
       }


   headers = {"auth-token": API_KEY}
   intensity = 250
   renewable_pct = "N/A"


   # 1. Fetch Carbon Intensity
   try:
       url_intensity = f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={ZONE}"
       resp_intensity = requests.get(url_intensity, headers=headers, timeout=10)
       if resp_intensity.status_code == 200:
           data = resp_intensity.json()
           intensity = data.get("carbonIntensity", 250)
   except Exception as e:
       print(f"Error fetching intensity API: {e}")


   # 2. Fetch Clean Energy Percentage
   try:
       url_cfer = f"https://api.electricitymap.org/v3/carbon-free-energy/latest?zone={ZONE}"
       resp_cfer = requests.get(url_cfer, headers=headers, timeout=10)
       if resp_cfer.status_code == 200:
           cfer_data = resp_cfer.json()
           val = cfer_data.get("value")
           if val is not None:
               renewable_pct = round(val, 1)
   except Exception as e:
       print(f"Error fetching carbon-free energy API: {e}")


   # 3. Fetch Free Weather Forecast via Open-Meteo
   forecast_message = fetch_open_meteo_green_window()


   # Determine visual state based on custom <150 threshold
   if intensity < 150:
       status = "green"
       message = "Eco-Friendly Window Open: Great time to run laundry, vacuum, or charge devices."
   elif 150 <= intensity <= 400:
       status = "yellow"
       message = "Moderate Grid Intensity: Balance power use and avoid heavy appliances if possible."
   else:
       status = "red"
       message = "Peak Emissions Alert: Minimize power use. Unplug vampire loads and delay EV charging."


   return {
       "zone": ZONE,
       "carbonIntensity": intensity,
       "renewablePercentage": renewable_pct,
       "forecastMessage": forecast_message,
       "status": status,
       "message": message
   }




# HTML Template with styling and forecast display box
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
   <meta charset="UTF-8">
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   <title>Carbon Weather Station</title>
   <meta http-equiv="refresh" content="900">
   <style>
       :root {
           --bg-green: #0f2e1a;
           --card-green: #1b4d2e;
           --text-green: #4ade80;


           --bg-yellow: #3b2f0f;
           --card-yellow: #594412;
           --text-yellow: #facc15;


           --bg-red: #3b1111;
           --card-red: #591b1b;
           --text-red: #f87171;
       }


       body {
           margin: 0;
           padding: 0;
           font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
           background-color: var(--bg-{{ status }});
           color: #ffffff;
           display: flex;
           justify-content: center;
           align-items: center;
           height: 100vh;
           transition: background-color 0.5s ease;
       }


       .container {
           background-color: var(--card-{{ status }});
           padding: 2.5rem;
           border-radius: 24px;
           box-shadow: 0 20px 40px rgba(0,0,0,0.4);
           text-align: center;
           max-width: 600px;
           width: 90%;
           transition: background-color 0.5s ease;
       }


       h1 {
           font-size: 1.4rem;
           text-transform: uppercase;
           letter-spacing: 2px;
           margin-bottom: 0.3rem;
           opacity: 0.8;
       }


       .zone {
           font-size: 0.9rem;
           opacity: 0.6;
           margin-bottom: 1.5rem;
       }


       .metric {
           font-size: 4.5rem;
           font-weight: 800;
           margin: 0.5rem 0;
           color: var(--text-{{ status }});
       }


       .unit {
           font-size: 1.3rem;
           font-weight: 400;
           opacity: 0.7;
       }


       .renewable {
           font-size: 1.1rem;
           margin-bottom: 1.2rem;
           opacity: 0.9;
       }


       .forecast-box {
           font-size: 1rem;
           background: rgba(0,0,0,0.25);
           padding: 0.8rem 1rem;
           border-radius: 8px;
           margin-bottom: 1.5rem;
           opacity: 0.95;
           border: 1px dashed rgba(255,255,255,0.2);
       }


       .message {
           font-size: 1.2rem;
           line-height: 1.4;
           background: rgba(0,0,0,0.2);
           padding: 1.2rem;
           border-radius: 12px;
           border-left: 6px solid var(--text-{{ status }});
       }
   </style>
</head>
<body>
   <div class="container">
       <h1>Live Grid Carbon Intensity</h1>
       <div class="zone">Grid Zone: {{ zone }}</div>


       <div class="metric">
           {{ carbonIntensity }} <span class="unit">gCO₂eq/kWh</span>
       </div>


       <div class="renewable">
           ⚡ Clean Energy Online: <strong>{{ renewablePercentage }}%</strong>
       </div>


       <div class="forecast-box">
           🌤️ {{ forecastMessage }}
       </div>


       <div class="message">
           {{ message }}
       </div>
   </div>
</body>
</html>
"""




@app.route("/")
def index():
   data = fetch_carbon_intensity()
   return render_template_string(HTML_TEMPLATE, **data)




@app.route("/api/data")
def api_data():
   return jsonify(fetch_carbon_intensity())




if __name__ == "__main__":
   app.run(host="0.0.0.0", port=5001, debug=True)
