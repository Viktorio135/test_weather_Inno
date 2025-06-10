from typing import Any
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, APIException
from rest_framework.request import Request

from .serializers import (
    CurrentWeatherSerializer, ForecastWeatherSerializer,
    ForecastCacheWeatherSerializer, CurrentWeatherResponseSerializer,
    ForecastWeatherResponseSerializer
)
from .services import WeatherService
from .providers import OpenMeteoWeatherProvider
from .repositories import CacheRepo


class CurrentWeatherView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.weather_service = WeatherService(
            providers=[OpenMeteoWeatherProvider()]
        )

    def get(self, request: Request) -> Response:
        """
        GET /api/weather/current:
        Возвращает текущую температуру и локальное время для указанного города.

        Параметры запроса:
            - city (str): Название города.

        Args:
            request (Request): Объект запроса Django REST Framework.

        Returns:
            Response: JSON с текущей температурой и локальным временем.
        """
        params_serializer = CurrentWeatherSerializer(
            data=request.query_params,
            context={'request': request}
        )
        params_serializer.is_valid(raise_exception=True)

        city: str = params_serializer.validated_data['city']

        status_code: int
        weather_data: dict[str, Any]
        status_code, weather_data = self.weather_service.get_current_weather(city)

        if status_code == status.HTTP_200_OK:
            response_serializer = CurrentWeatherResponseSerializer(data=weather_data)
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data)

        self.handle_error(status_code)

    def handle_error(self, status_code: int):
        match status_code:
            case status.HTTP_404_NOT_FOUND:
                raise NotFound(detail='Город не найден')
            case status.HTTP_503_SERVICE_UNAVAILABLE:
                raise APIException(
                    detail='Ошибка соединения с сервисом погоды.',
                    code=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            case status.HTTP_504_GATEWAY_TIMEOUT:
                raise APIException(
                    detail='Время ожидания истекло при обращении к сервису погоды.',
                    code=status.HTTP_504_GATEWAY_TIMEOUT
                )
            case status.HTTP_500_INTERNAL_SERVER_ERROR:
                raise APIException(
                    detail='Внутренняя ошибка сервиса погоды.',
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            case _:
                raise APIException(
                    detail='Неизвестная ошибка при получении погоды.',
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )


class ForecastWeatherView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.weather_service = WeatherService(
            providers=[OpenMeteoWeatherProvider()]
        )

    def get(self, request: Request) -> Response:
        """
        GET /api/weather/forecast:
        Возвращает прогноз температуры на заданную дату для указанного города.

        Параметры запроса:
            - city (str): Название города.
            - date (str): Дата прогноза в формате YYYY-MM-DD.

        Args:
            request (Request): Объект запроса Django REST Framework.

        Returns:
            Response: JSON с прогнозом температуры.
        """
        params_serializer = ForecastWeatherSerializer(
            data=request.query_params,
            context={'request': request}
        )
        params_serializer.is_valid(raise_exception=True)

        city: str = params_serializer.validated_data['city']
        date: str = params_serializer.validated_data['date']

        cache = CacheRepo().get(city=city, date={
            "city": city,
            "date": date
        })

        if cache:
            return Response(
                {
                    "min_temperature": cache.min_temperature,
                    "max_temperature": cache.max_temperature
                }
            )

        status_code: int
        weather_data: dict[str, Any]
        status_code, weather_data = self.weather_service.get_forecast_weather(city, date)

        if status_code == status.HTTP_200_OK:
            response_serializer = ForecastWeatherResponseSerializer(data=weather_data)
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data)

        self.handle_error(status_code)

    def post(self, request: Request):
        """
        POST /api/weather/forecast:
        Позволяет вручную задать или переопределить прогноз погоды для указанного города и даты.

        Параметры запроса:
            - city (str): Название города.
            - date (str): Дата прогноза в формате YYYY-MM-DD.
            - temperature (float): Прогнозируемая температура.

        Args:
            request (Request): Объект запроса Django REST Framework.

        Returns:
            Response: JSON с сообщением об успешной обработке и флагом created.
        """
        params_serializer = ForecastCacheWeatherSerializer(
            data=request.data,
            context={'request': request}
        )
        params_serializer.is_valid(raise_exception=True)

        validated_data: dict[str, Any] = params_serializer.validated_data

        lookup = {
            'city': validated_data['city'],
            'date': validated_data['date']
        }

        defaults = {
            key: value for key, value in validated_data.items() if key not in lookup
        }

        obj, created = CacheRepo().create_or_update(
            lookup=lookup,
            defaults=defaults
        )

        return Response({'message': 'OK', 'created': created})

    def handle_error(self, status_code: int):
        match status_code:
            case status.HTTP_404_NOT_FOUND:
                raise NotFound(detail='Город не найден')
            case status.HTTP_503_SERVICE_UNAVAILABLE:
                raise APIException(
                    detail='Ошибка соединения с сервисом погоды.',
                    code=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            case status.HTTP_504_GATEWAY_TIMEOUT:
                raise APIException(
                    detail='Время ожидания истекло при обращении к сервису погоды.',
                    code=status.HTTP_504_GATEWAY_TIMEOUT
                )
            case status.HTTP_500_INTERNAL_SERVER_ERROR:
                raise APIException(
                    detail='Внутренняя ошибка сервиса погоды.',
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            case _:
                raise APIException(
                    detail='Неизвестная ошибка при получении прогноза погоды.',
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
