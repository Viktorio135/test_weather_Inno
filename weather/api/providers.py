import requests

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class WeatherProvider(ABC):
    @abstractmethod
    def get_current_weather(self, city: str) -> tuple[int, Optional[Dict[str, Any]]]:
        """
        Получает текущую температуру и локальное время для указанного города.
        Возвращает кортеж: (HTTP status code, данные или None)
        """
        pass

    @abstractmethod
    def get_forecast_weather(self, city: str, date: str) -> tuple[int, Optional[Dict[str, Any]]]:
        """
        Получает прогноз погоды на указанную дату для указанного города.
        Возвращает кортеж: (HTTP status code, данные или None)
        """
        pass


class OpenMeteoWeatherProvider(WeatherProvider):
    def _get_geocoding(self, city: str) -> tuple[int, Optional[Dict[str, Any]]]:
        geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        try:
            response = requests.get(geocoding_url, timeout=5)
            response.raise_for_status()
            geo_data = response.json()

            if 'results' not in geo_data or not geo_data['results']:
                return 404, None

            result = geo_data['results'][0]
            return 200, {
                'latitude': result['latitude'],
                'longitude': result['longitude'],
                'timezone': result.get('timezone', 'auto')
            }
        except requests.exceptions.ConnectionError:
            return 503, None
        except requests.exceptions.Timeout:
            return 504, None
        except requests.exceptions.RequestException:
            return 500, None

    def _get_local_time(self, offset_seconds):
        offset = timedelta(seconds=offset_seconds)
        local_time = datetime.now() + offset
        return local_time.strftime('%H:%M')

    def get_current_weather(self, city: str) -> tuple[int, Optional[Dict[str, Any]]]:
        geo_status, geo_data = self._get_geocoding(city)
        if geo_status != 200 or geo_data is None:
            return geo_status, None

        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={geo_data['latitude']}"
            f"&longitude={geo_data['longitude']}"
            f"&current_weather=true"
            f"&timezone={geo_data['timezone']}"
        )
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            temperature = data["current_weather"]["temperature"]
            offset_seconds = data.get("utc_offset_seconds", 0)
            local_time = self._get_local_time(offset_seconds)

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

    def get_forecast_weather(self, city: str, date: str) -> tuple[int, Optional[Dict[str, Any]]]:
        geo_status, geo_data = self._get_geocoding(city)
        if geo_status != 200 or geo_data is None:
            return geo_status, None

        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={geo_data['latitude']}"
            f"&longitude={geo_data['longitude']}"
            f"&daily=temperature_2m_min,temperature_2m_max"
            f"&forecast_days=10"
            f"&timezone={geo_data['timezone']}"
        )
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            forecast_data = response.json()

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
