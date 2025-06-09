from rest_framework import status
from django.http import JsonResponse

from .repositories import CacheRepo
from .serializers import ForecastWeatherSerializer


class CacheMiddleware:
    """
    Middleware для кэширования GET-запросов к эндпоинту прогноза погоды (/api/weather/forecast/).
    Если данные прогноза уже есть в кеше,
    то возвращает их напрямую, минуя обработку запроса во view.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/api/weather/forecast/' and request.method == 'GET':
            query_params = request.GET

            serializer = ForecastWeatherSerializer(data=query_params)
            if not serializer.is_valid():
                return JsonResponse(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            validated_data = serializer.validated_data
            city = validated_data['city']
            date_obj = validated_data['date']

            cache = CacheRepo().get(city=city, date=date_obj)

            if cache:
                return JsonResponse(
                    {
                        "min_temperature": cache.min_temperature,
                        "max_temperature": cache.max_temperature
                    }
                )

        response = self.get_response(request)
        return response
