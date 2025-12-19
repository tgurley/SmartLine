import requests
from datetime import datetime

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"

city = "Washington"
state = "DC"

# 2023-10-05 7:15 PM ET → 23:15 UTC (hour-aligned to 23:00)
game_time_utc = datetime(2023, 10, 5, 23, 0)

# Step 1: Geocode
geo = requests.get(
    "https://geocoding-api.open-meteo.com/v1/search",
    params={
        "name": city,
        "state": state,
        "country": "US",
        "count": 1
    },
    timeout=20
).json()

lat = geo["results"][0]["latitude"]
lon = geo["results"][0]["longitude"]

# Step 2: Weather request (ARCHIVE DATA)
params = {
    "latitude": lat,
    "longitude": lon,
    "hourly": [
        "temperature_2m",
        "wind_speed_10m",
        "precipitation"      # ✅ amount in mm
    ],
    "start_date": "2023-10-05",
    "end_date": "2023-10-06",
    "timezone": "UTC"
}

weather = requests.get(OPEN_METEO_URL, params=params, timeout=20).json()
print(weather)
hourly = weather.get("hourly", {})

times = hourly.get("time", [])
temps = hourly.get("temperature_2m", [])
winds = hourly.get("wind_speed_10m", [])
precips = hourly.get("precipitation", [])

# Step 3: Find kickoff hour
for i, t in enumerate(times):
    if t == "2023-10-05T23:00":
        print("Time:", t)
        print("Temp (°C):", temps[i])
        print("Wind (m/s):", winds[i])
        print("Precip (mm):", precips[i])

