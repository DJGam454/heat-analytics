import requests
import os

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("WEATHER_API_KEY")


def get_weather_data(lat, lon, run_date, run_hour):

    url = (
        f"https://api.weatherapi.com/v1/history.json"
        f"?key={API_KEY}"
        f"&q={lat},{lon}"
        f"&dt={run_date}"
    )

    response = requests.get(url)

    print("Status Code:", response.status_code)
    print("Response:", response.text)

    if response.status_code != 200:
        return None

    data = response.json()

    try:

        hourly_data = data["forecast"]["forecastday"][0]["hour"]

        closest_hour = hourly_data[run_hour]

        weather = {
            "temp_c": closest_hour["temp_c"],
            "feelslike_c": closest_hour["feelslike_c"],
            "humidity": closest_hour["humidity"],
            "wind_kph": closest_hour["wind_kph"],
            "condition": closest_hour["condition"]["text"]
        }

        return weather

    except Exception:
        return None