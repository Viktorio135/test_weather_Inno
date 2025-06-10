from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, APIException

from .serializers import (
    CurrentWeatherSerializer, ForecastWeatherSerializer,
    ForecastCacheWeatherSerializer, CurrentWeatherResponseSerializer,
    ForecastWeatherResponseSerializer
)
from .utils import get_current_weather, get_forecast_weather
from .repositories import CacheRepo


class CurrentWeatherView(APIView):
    def get(self, request):
        """
        Эндпоинт GET /api/weather/current:
        Возвращает текущую температуру и локальное время для указанного города.
        """
        params_serializer = CurrentWeatherSerializer(
            data=request.query_params,
            context={'request': request}
        )
        params_serializer.is_valid(raise_exception=True)

        city = params_serializer.validated_data['city']

        status_code, weather_data = get_current_weather(city)

        if status_code == status.HTTP_200_OK:
            response_serializer = CurrentWeatherResponseSerializer(data=weather_data)
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data)

        elif status_code == status.HTTP_404_NOT_FOUND:
            raise NotFound(detail='Город не найден')
        elif status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            raise APIException(
                detail='Ошибка соединения с сервисом погоды.',
                code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        elif status_code == status.HTTP_504_GATEWAY_TIMEOUT:
            raise APIException(
                detail='Время ожидания истекло при обращении к сервису погоды.',
                code=status.HTTP_504_GATEWAY_TIMEOUT
            )
        elif status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise APIException(
                detail='Внутренняя ошибка сервиса погоды.',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        else:
            raise APIException(
                detail='Неизвестная ошибка при получении погоды.',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ForecastWeatherView(APIView):
    def get(self, request):
        """
        Эндпоинт GET /api/weather/forecast:
        Возвращает прогноз температуры на заданную дату для указанного города.
        """
        params_serializer = ForecastWeatherSerializer(
            data=request.query_params,
            context={'request': request}
        )
        params_serializer.is_valid(raise_exception=True)

        city = params_serializer.validated_data['city']
        date = params_serializer.validated_data['date']

        status_code, weather_data = get_forecast_weather(city, date)

        if status_code == status.HTTP_200_OK:
            response_serializer = ForecastWeatherResponseSerializer(data=weather_data)
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data)

        elif status_code == status.HTTP_404_NOT_FOUND:
            raise NotFound(detail='Город не найден')
        elif status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            raise APIException(
                detail='Ошибка соединения с сервисом погоды.',
                code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        elif status_code == status.HTTP_504_GATEWAY_TIMEOUT:
            raise APIException(
                detail='Время ожидания истекло при обращении к сервису погоды.',
                code=status.HTTP_504_GATEWAY_TIMEOUT
            )
        elif status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise APIException(
                detail='Внутренняя ошибка сервиса погоды.',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        else:
            raise APIException(
                detail='Неизвестная ошибка при получении погоды.',
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """
        Эндпоинт POST /api/weather/forecast:
        Позволяет вручную задать или переопределить прогноз погоды для указанного города и даты.
        """
        params_serializer = ForecastCacheWeatherSerializer(
            data=request.data,
            context={'request': request}
        )
        params_serializer.is_valid(raise_exception=True)

        validated_data = params_serializer.validated_data

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
