Для получения **реальных данных** о погоде используется внешний API:
- **OpenWeatherMap** — [https://openweathermap.org/](https://openweathermap.org/)
Для доступа к OpenWeatherMap необходим API-ключ, который указывается в файле `.env`


## Запуск проекта

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2.	Создайте файл .env, добавьте ключ OpenWeatherMap и SECRET_KEY
3. Выполните миграции:
   ```bash
   python manage.py migrate
   ```
4.	Запустите сервер:
   ```bash
   python manage.py runserver
   ```