import requests
from datetime import datetime, timedelta


def get_local_time(offset_seconds):
    """
    Получение локального времени, с помощью разницы с GMT
    """
    offset = timedelta(seconds=offset_seconds)
    local_time = datetime.now() + offset
    return local_time.strftime('%H:%M')


def get_geocoding(city):
    """
    Получает геокоординаты для указанного города.
    Использует Open-Meteo API.
    """
    geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
    try:
        geo_response = requests.get(geocoding_url, timeout=5)
        geo_response.raise_for_status()
        geo_data = geo_response.json()

        if 'results' not in geo_data or len(geo_data['results']) == 0:
            return 404, None

        result = geo_data['results'][0]
        latitude = result['latitude']
        longitude = result['longitude']
        timezone_name = result.get('timezone', 'auto')
        return 200, (latitude, longitude, timezone_name)

    except requests.exceptions.ConnectionError:
        return 503, None
    except requests.exceptions.Timeout:
        return 504, None
    except requests.exceptions.RequestException:
        return 500, None


def get_forecast_weather(city, date):
    """
    Получает прогноз погоды на указанную дату для указанного города.
    Использует Open-Meteo API.
    """
    geo_status, geo_data = get_geocoding(city)
    if geo_status != 200 or geo_data is None:
        return geo_status, None

    latitude, longitude, timezone_name = geo_data

    forecast_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        f"&daily=temperature_2m_min,temperature_2m_max"
        f"&forecast_days=10"
        f"&timezone={timezone_name}"
    )
    try:
        forecast_response = requests.get(forecast_url, timeout=5)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()

        dates = forecast_data['daily']['time']
        min_temps = forecast_data['daily']['temperature_2m_min']
        max_temps = forecast_data['daily']['temperature_2m_max']

        for i, forecast_date in enumerate(dates):
            if forecast_date == str(date):
                return 200, {
                    "min_temperature": min_temps[i],
                    "max_temperature": max_temps[i]
                }

        return 404, None

    except requests.exceptions.ConnectionError:
        return 503, None
    except requests.exceptions.Timeout:
        return 504, None
    except requests.exceptions.RequestException:
        return 500, None


def get_current_weather(city):
    """
    Получает текущую температуру и локальное время для указанного города.
    Использует Open-Meteo API.
    """
    geo_status, geo_data = get_geocoding(city)
    if geo_status != 200 or geo_data is None:
        return geo_status, None

    latitude, longitude, timezone_name = geo_data

    weather_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}"
        f"&longitude={longitude}"
        f"&current_weather=true"
        f"&timezone={timezone_name}"
    )
    try:
        weather_response = requests.get(weather_url, timeout=5)
        weather_response.raise_for_status()
        data = weather_response.json()

        temperature = data["current_weather"]["temperature"]
        offset_seconds = data.get("utc_offset_seconds", 0)
        local_time = get_local_time(offset_seconds)

        return 200, {
            "temperature": temperature,
            "local_time": local_time
        }

    except requests.exceptions.ConnectionError:
        return 503, None
    except requests.exceptions.Timeout:
        return 504, None
    except requests.exceptions.RequestException:
        return 500, None
