# Prize Roulette Web App

Веб-приложение для розыгрыша призов с интеграцией Telegram.

## Функциональность

- Рулетка с призами
- Интеграция с Telegram ботом
- Админ-панель для управления призами
- API для взаимодействия с ботом
- Система учета попыток пользователей

## Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/your-username/prize-roulette-web.git
cd prize-roulette-web
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` с настройками:
```env
DATABASE_URL=sqlite+aiosqlite:///prizes.db
ADMIN_TOKEN=your_secure_admin_token
BOT_TOKEN=your_bot_token
DEBUG=false
```

4. Примените миграции базы данных:
```bash
alembic upgrade head
```

5. Запустите приложение:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Структура проекта

```
prize-roulette-web/
├── main.py            # Основной файл приложения
├── config.py          # Конфигурация
├── api_routes.py      # API роуты
├── requirements.txt   # Зависимости
├── static/           # Статические файлы
│   ├── style.css
│   ├── roulette.js
│   └── admin.js
├── templates/        # HTML шаблоны
│   ├── index.html
│   └── admin.html
├── assets/          # Изображения призов
└── images/          # Дополнительные изображения
```

## API Endpoints

- `GET /api/prizes/{user_id}` - получение призов пользователя
- `POST /api/spin/{user_id}` - крутить рулетку
- `GET /api/spins/{user_id}/available` - проверка доступности попыток
- `GET /admin` - админ-панель
- `GET /health` - проверка работоспособности

## Требования

- Python 3.8+
- FastAPI
- SQLAlchemy
- База данных (SQLite по умолчанию)

## Разработка

1. Установите зависимости для разработки:
```bash
pip install -r requirements.dev.txt
```

2. Запустите тесты:
```bash
pytest
```

## Деплой

1. Настройте переменные окружения на сервере
2. Установите зависимости
3. Настройте базу данных
4. Запустите через Gunicorn или uvicorn

## Лицензия

MIT 