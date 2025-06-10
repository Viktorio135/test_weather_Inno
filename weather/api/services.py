from typing import Any, Dict, Optional
from .providers import WeatherProvider


class WeatherService:
    def __init__(self, providers: list[WeatherProvider]):
        self.providers = providers

    def get_current_weather(self, city: str) -> tuple[int, Optional[Dict[str, Any]]]:
        for provider in self.providers:
            status, data = provider.get_current_weather(city)
            if status == 200:
                return status, data
        return status, None

    def get_forecast_weather(self, city: str, date: str) -> tuple[int, Optional[Dict[str, Any]]]:
        for provider in self.providers:
            status, data = provider.get_forecast_weather(city, date)
            if status == 200:
                return status, data
        return status, None
