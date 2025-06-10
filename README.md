Для получения **реальных данных** о погоде используется внешний API:
- **open-meteo** — [https://open-meteo.com/](https://open-meteo.com/)


## Запуск проекта

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2.	Создайте файл .env, добавьте ключ SECRET_KEY
3. Выполните миграции:
   ```bash
   python manage.py migrate
   ```
4.	Запустите сервер:
   ```bash
   python manage.py runserver
   ```