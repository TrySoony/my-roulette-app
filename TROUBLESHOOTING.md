# Устранение неполадок развертывания

## Проблема: TypeError: FastAPI.__call__() missing 1 required positional argument: 'send'

### Причина
Gunicorn пытается использовать FastAPI приложение как WSGI приложение, но FastAPI - это ASGI приложение.

### Решение 1: Использовать Uvicorn напрямую (рекомендуется)
```bash
# Procfile
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

### Решение 2: Использовать Gunicorn с ASGI воркером
```bash
# Procfile
web: gunicorn app:app --bind 0.0.0.0:$PORT --worker-class uvicorn.workers.UvicornWorker --workers 1
```

## Проверка работоспособности

### 1. Проверка импорта
```bash
python -c "from app import app; print('✅ Приложение импортировано успешно')"
```

### 2. Проверка локального запуска
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 3. Проверка эндпоинтов
- `GET /` - главная страница
- `GET /health` - проверка здоровья
- `POST /webhook` - webhook для Telegram бота

## Переменные окружения

Убедитесь, что установлены все необходимые переменные окружения в Render:

```bash
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_admin_user_id
RENDER_EXTERNAL_URL=https://your-app-name.onrender.com
WEBHOOK_SECRET=your_webhook_secret
MAX_ATTEMPTS=2
DEBUG=false
```

## Логи

Для просмотра логов в Render:
1. Перейдите в панель управления Render
2. Выберите ваш сервис
3. Перейдите на вкладку "Logs"

## Частые ошибки

### 1. ModuleNotFoundError: No module named 'app'
- Убедитесь, что файл `app.py` существует
- Проверьте, что `app.py` импортирует приложение из `main.py`

### 2. ImportError при загрузке конфигурации
- Проверьте переменные окружения
- Убедитесь, что `config.py` корректно настроен

### 3. Ошибки с зависимостями
- Проверьте `requirements.txt`
- Убедитесь, что все зависимости установлены

## Структура файлов для развертывания

```
├── app.py              # Точка входа для Gunicorn/Uvicorn
├── main.py             # Основное FastAPI приложение
├── config.py           # Конфигурация
├── requirements.txt    # Зависимости Python
├── Procfile           # Команда запуска для Render
├── runtime.txt        # Версия Python
└── static files...    # HTML, CSS, JS файлы
``` 