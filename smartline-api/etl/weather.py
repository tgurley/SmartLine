import requests
from datetime import timedelta, datetime, timezone
from etl.db import get_conn

OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"


def load_weather():
    conn = get_conn()
    cur = conn.cursor()

    print("🌦️ Loading kickoff-time weather data...")

    # ------------------------------------------------------
    # Pull games with venue info
    # ------------------------------------------------------
    cur.execute("""
        SELECT
            g.game_id,
            g.game_datetime_utc,
            v.city,
            v.state,
            v.is_dome
        FROM game g
        JOIN venue v ON g.venue_id = v.venue_id
        WHERE g.game_id NOT IN (
            SELECT game_id FROM weather_observation
        )
        ORDER BY g.game_datetime_utc;
    """)

    games = cur.fetchall()
    print(f"📦 Games needing weather: {len(games)}")

    inserted = 0
    skipped = 0

    for game_id, kickoff_utc, city, state, is_dome in games:

        # -------------------------------
        # Dome handling
        # -------------------------------
        if is_dome:
            cur.execute("""
                INSERT INTO weather_observation (
                    game_id,
                    temp_f,
                    wind_mph,
                    precip_prob,
                    precip_mm,
                    conditions,
                    observed_at_utc,
                    source,
                    is_cold,
                    is_hot,
                    is_windy,
                    is_heavy_wind,
                    is_rain_risk,
                    is_storm_risk,
                    weather_severity_score
                )
                VALUES (
                    %s,
                    NULL,
                    NULL,
                    NULL,
                    0,
                    'dome',
                    %s,
                    'dome',
                    FALSE,
                    FALSE,
                    FALSE,
                    FALSE,
                    FALSE,
                    FALSE,
                    0
                )
                ON CONFLICT DO NOTHING;
            """, (game_id, kickoff_utc))

            if cur.rowcount == 1:
                inserted += 1
            continue

        # -------------------------------
        # Outdoor game → Open-Meteo ARCHIVE
        # -------------------------------
        date_str = kickoff_utc.date().isoformat()

        params = {
            "latitude": None,
            "longitude": None,
            "hourly": "temperature_2m,wind_speed_10m,precipitation",
            "start_date": date_str,
            "end_date": date_str,
            "timezone": "UTC"
        }

        # Geocoding
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "state": state, "country": "US", "count": 1},
            timeout=20
        ).json()

        if not geo.get("results"):
            skipped += 1
            continue

        params["latitude"] = geo["results"][0]["latitude"]
        params["longitude"] = geo["results"][0]["longitude"]

        weather = requests.get(OPEN_METEO_URL, params=params, timeout=20).json()
        hourly = weather.get("hourly", {})

        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        winds = hourly.get("wind_speed_10m", [])
        precips_mm = hourly.get("precipitation", [])

        if not times:
            skipped += 1
            continue

        # Find hour closest to kickoff
        kickoff_hour = kickoff_utc.replace(minute=0, second=0, microsecond=0)

        def parse_utc(ts):
            return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)

        idx = min(
            range(len(times)),
            key=lambda i: abs(kickoff_hour - parse_utc(times[i]))
        )

        # Convert Celsius → Fahrenheit
        temp_c = temps[idx]
        temp_f = (temp_c * 9.0 / 5.0) + 32 if temp_c is not None else None

        wind = winds[idx]
        precip_mm = precips_mm[idx]

        # -------------------------------
        # Severity flags (UPDATED LOGIC)
        # -------------------------------
        is_cold = temp_f is not None and temp_f <= 32
        is_hot = temp_f is not None and temp_f >= 85
        is_windy = wind is not None and wind >= 15
        is_heavy_wind = wind is not None and wind >= 25

        # Rain risk now based on ACTUAL precipitation
        is_rain_risk = precip_mm is not None and precip_mm >= 1.0
        is_storm_risk = precip_mm is not None and precip_mm >= 5.0

        severity_score = (
            (2 if is_cold else 0) +
            (2 if is_hot else 0) +
            (2 if is_windy else 0) +
            (3 if is_heavy_wind else 0) +
            (2 if is_rain_risk else 0) +
            (3 if is_storm_risk else 0)
        )

        cur.execute("""
            INSERT INTO weather_observation (
                game_id,
                temp_f,
                wind_mph,
                precip_prob,
                precip_mm,
                conditions,
                observed_at_utc,
                source,
                is_cold,
                is_hot,
                is_windy,
                is_heavy_wind,
                is_rain_risk,
                is_storm_risk,
                weather_severity_score
            )
            VALUES (
                %s, %s, %s,
                NULL,
                %s,
                NULL,
                %s,
                'open-meteo',
                %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT DO NOTHING;
        """, (
            game_id,
            temp_f,
            wind,
            precip_mm,
            kickoff_hour,
            is_cold,
            is_hot,
            is_windy,
            is_heavy_wind,
            is_rain_risk,
            is_storm_risk,
            severity_score
        ))

        if cur.rowcount == 1:
            inserted += 1

    conn.commit()
    cur.close()
    conn.close()

    print(f"✅ Weather ETL complete — inserted={inserted}, skipped={skipped}")


if __name__ == "__main__":
    load_weather()

