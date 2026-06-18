from django.http import JsonResponse
import requests

def get_external_data(request):
    params = {
        "latitude": 43.286,
        "longitude": 20.8092,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "snowfall",
            "weather_code",
            "cloud_cover",
            "wind_speed_10m",
            "apparent_temperature",     
            "wind_direction_10m",       
        ],
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "snowfall",
        ],
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "rain_sum",
            "snowfall_sum",
            "wind_speed_10m_max",
            "apparent_temperature_mean",
            "wind_direction_10m_dominant",
        ],
    }

    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params=params
    )
    return JsonResponse(response.json())