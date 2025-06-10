from django.urls import path

from .views import CurrentWeatherView, ForecastWeatherView


app_name = 'api'

urlpatterns = [
    path('current/', CurrentWeatherView.as_view()),
    path("forecast/", ForecastWeatherView.as_view()),
]
