from rest_framework import serializers

from datetime import date, timedelta


class CurrentWeatherSerializer(serializers.Serializer):
    """
    Сериализатор для валидации входных данных текущей погоды.
    """
    city = serializers.CharField(required=True, max_length=20)


class CurrentWeatherResponseSerializer(serializers.Serializer):
    """
    Сериализатор для валидации выходных данных текущей погоды.
    """
    temperature = serializers.FloatField(required=True)
    local_time = serializers.TimeField(format='%H:%M')


class ForecastWeatherSerializer(serializers.Serializer):
    """
    Сериализатор для валидации входных данных погоды на определенную дату.
    """
    city = serializers.CharField(required=True, max_length=20)
    date = serializers.DateField(
        required=True,
        input_formats=['%d.%m.%Y'],
        format='%Y-%m-%d'
    )

    def validate_date(self, value):
        """
        Проверка: ограничение по времени.
        """
        today = date.today()
        max_date = today + timedelta(days=10)
        if value < today:
            raise serializers.ValidationError("Дата не может быть в прошлом.")
        if value > max_date:
            raise serializers.ValidationError("Дата не может быть более чем через 10 дней.")
        return value


class ForecastWeatherResponseSerializer(serializers.Serializer):
    """
    Сериализатор для валидации выходных данных погоды на определенную дату.
    """
    min_temperature = serializers.FloatField()
    max_temperature = serializers.FloatField()


class ForecastCacheWeatherSerializer(serializers.Serializer):
    """
    Сериализатор для валидации входных данных погоды на определенную дату для кэширования.
    """
    city = serializers.CharField(required=True, max_length=20)
    date = serializers.DateField(
        required=True,
        input_formats=['%d.%m.%Y'],
        format='%Y-%m-%d'
    )
    min_temperature = serializers.FloatField(required=True)
    max_temperature = serializers.FloatField(required=True)

    def validate_date(self, value):
        """
        Проверка: ограничение по времени.
        """
        today = date.today()
        max_date = today + timedelta(days=10)
        if value < today:
            raise serializers.ValidationError("Дата не может быть в прошлом.")
        if value > max_date:
            raise serializers.ValidationError("Дата не может быть более чем через 10 дней.")
        return value

    def validate(self, attrs):
        """
        Проверка: min_temperature не может быть больше max_temperature.
        """
        if attrs["min_temperature"] > attrs["max_temperature"]:
            raise serializers.ValidationError('Минимальная температура не может быть больше максимальной')
        return attrs
