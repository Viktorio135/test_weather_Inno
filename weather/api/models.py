from django.db import models


class Сache(models.Model):
    """
    Модель для хранения переопределённых данных прогноза погоды
    для конкретного города и даты.
    """
    city = models.CharField(max_length=50)
    date = models.DateField()
    min_temperature = models.FloatField()
    max_temperature = models.FloatField()
