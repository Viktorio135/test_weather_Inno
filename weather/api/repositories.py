from .models import Сache


class BaseRepo:
    def __init__(self, model):
        self.model = model

    def get(self, **kwargs):
        """Получить один объект по фильтру"""
        try:
            return self.model.objects.get(**kwargs)
        except self.model.DoesNotExist:
            return None

    def filter(self, **kwargs):
        """Получить QuerySet объектов по фильтру"""
        return self.model.objects.filter(**kwargs)

    def create(self, **kwargs):
        """Создать объект"""
        return self.model.objects.create(**kwargs)

    def update(self, instance, **kwargs):
        """Обновить поля объекта"""
        for attr, value in kwargs.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def create_or_update(self, lookup, defaults=None):
        """Создание нового объекта, или его обновление"""
        defaults = defaults or {}
        obj, created = self.model.objects.update_or_create(defaults=defaults, **lookup)
        return obj, created

    def delete(self, instance):
        """Удалить объект"""
        instance.delete()

    def all(self):
        """Получить все объекты"""
        return self.model.objects.all()


class CacheRepo(BaseRepo):
    def __init__(self):
        super().__init__(model=Сache)
