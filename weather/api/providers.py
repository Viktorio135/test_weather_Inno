import requests

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from .repositories import CacheRepo


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


class CacheWeatherProvider(WeatherProvider):
    """
    Кэширующий провайдер.
    """

    def get_current_weather(self, city: str) -> tuple[int, Optional[Dict[str, Any]]]:
        """
        Метод не реализован, так как данный провайдер кэширует только прогноз.
        """
        raise NotImplementedError("Метод get_current_weather не поддерживается в кэширующем провайдере")

    def get_forecast_weather(self, city: str, date: str) -> Tuple[int, Optional[Dict[str, Any]]]:
        """
        Получает прогноз погоды (минимальная и максимальная температура) на указанную дату для указанного города.

        Данные берутся из кэша, если они есть. Если данных в кэше нет, возвращает (404, None).

        Args:
            city (str): Название города.
            date (str): Дата прогноза в формате 'YYYY-MM-DD'.

        Returns:
            tuple[int, Optional[Dict[str, Any]]]:
                - 200: Данные найдены в кэше.
                - 404: Данные отсутствуют в кэше.
                - forecast_data (dict | None):
                    - 'min_temperature': минимальная температура.
                    - 'max_temperature': максимальная температура.
        """
        cache = CacheRepo().get(city=city, date=date)
        if cache:
            return 200, {
                        "min_temperature": cache.min_temperature,
                        "max_temperature": cache.max_temperature
                    }

        return 404, None


class OpenMeteoWeatherProvider(WeatherProvider):
    """
    Провайдер погоды на основе Open-Meteo API.
    """
    def _get_geocoding(self, city: str) -> tuple[int, Optional[Dict[str, Any]]]:
        """
        Получает географические координаты (широту, долготу) и таймзону для указанного города.

        Args:
            city (str): Название города.

        Returns:
            tuple[int, Optional[Dict[str, Any]]]:
                - status_code (int): HTTP статус (200, 404, 503, 504, 500).
                - geo_data (dict | None): Словарь с ключами:
                    - 'latitude': широта города
                    - 'longitude': долгота города
                    - 'timezone': часовой пояс
                  Или None, если данные не найдены или произошла ошибка.
        """
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
        """
        Рассчитывает локальное время на основе смещения в секундах.

        Args:
            offset_seconds (int): Смещение в секундах относительно UTC.

        Returns:
            str: Локальное время в формате 'HH:MM'.
        """
        offset = timedelta(seconds=offset_seconds)
        local_time = datetime.now() + offset
        return local_time.strftime('%H:%M')

    def get_current_weather(self, city: str) -> tuple[int, Optional[Dict[str, Any]]]:
        """
        Получает текущую температуру и локальное время для указанного города.

        Args:
            city (str): Название города.

        Returns:
            tuple[int, Optional[Dict[str, Any]]]:
                - status_code (int): HTTP статус (200, 404, 503, 504, 500).
                - weather_data (dict | None): Словарь с ключами:
                    - 'temperature': текущая температура
                    - 'local_time': локальное время
                  Или None, если данные не найдены или произошла ошибка.
        """
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

            current_weather = data.get("current_weather")
            if not current_weather or "temperature" not in current_weather:
                return 500, None

            temperature = current_weather["temperature"]
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
        """
        Получает прогноз погоды (минимальную и максимальную температуру) на указанную дату для города.

        Args:
            city (str): Название города.
            date (str): Дата прогноза в формате 'YYYY-MM-DD'.

        Returns:
            tuple[int, Optional[Dict[str, Any]]]:
                - status_code (int): HTTP статус (200, 404, 503, 504, 500).
                - forecast_data (dict | None): Словарь с ключами:
                    - 'min_temperature': минимальная температура
                    - 'max_temperature': максимальная температура
                  Или None, если данные не найдены или произошла ошибка.
        """
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

            daily_data = forecast_data.get("daily")
            if not daily_data:
                return 500, None

            dates = daily_data.get('time', [])
            min_temps = daily_data.get('temperature_2m_min', [])
            max_temps = daily_data.get('temperature_2m_max', [])

            if not (dates and min_temps and max_temps):
                return 500, None

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
