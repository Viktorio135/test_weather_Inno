import requests


from datetime import datetime, timedelta, timezone
from django.conf import settings


def get_local_time(offset_seconds):
    """
    Получает локальное время для города на основе смещения от UTC в секундах.
    :param offset_seconds: Смещение в секундах от UTC.
    :return: Строка с локальным временем в формате HH:MM.
    """
    offset = timezone(timedelta(seconds=offset_seconds))
    utc_time = datetime.now()
    local_time = utc_time.replace(tzinfo=timezone.utc).astimezone(offset)
    return local_time.strftime('%H:%M')


def get_date_weather(data, target_date):
    """
    Извлекает минимальную и максимальную температуру из прогноза погоды на указанную дату.
    :param data: JSON-ответ от API прогноза погоды (OpenWeather).
    :param target_date: Целевая дата прогноза.
    :return: Кортеж (min_temp, max_temp) или (None, None) если данных нет.
    """
    min_temp = float('inf')
    max_temp = float('-inf')

    for entry in data['list']:
        dt_txt = entry['dt_txt']
        date_part = dt_txt.split()[0]

        if date_part == str(target_date):
            temp_min = entry['main']['temp_min']
            temp_max = entry['main']['temp_max']
            min_temp = min(min_temp, temp_min)
            max_temp = max(max_temp, temp_max)

    if min_temp != float('inf') and max_temp != float('-inf'):
        return min_temp, max_temp
    return None, None


def get_current_weather(city):
    """
    Получает текущую температуру и локальное время для указанного города.
    :param city: Название города на английском языке.
    :return: Кортеж (status_code, данные) или (status_code, None) при ошибке.
    """
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={settings.WEATHER_API_KEY}&units=metric"
    response = requests.get(url, timeout=5)
    status_code = response.status_code
    if status_code == 200:
        data = response.json()
        temperature = data["main"]["temp"]
        local_time = get_local_time(data["timezone"])
        return status_code, {
            "temperature": temperature,
            "local_time": local_time
        }
    return status_code, None


def get_forecast_weather(city, date):
    """
    Получает прогноз погоды (мин и макс температура) для указанного города на определённую дату.
    :param city: Название города на английском языке.
    :param date: Дата прогноза.
    :return: Кортеж (status_code, данные) или (status_code, None) при ошибке.
    """
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={settings.WEATHER_API_KEY}"
    response = requests.get(url, timeout=5)
    status_code = response.status_code
    if response.status_code == 200:
        data = response.json()
        min_temp, max_temp = get_date_weather(data, date)
        return status_code, {
            "min_temperature": min_temp,
            "max_temperature": max_temp
        }
    return status_code, None
