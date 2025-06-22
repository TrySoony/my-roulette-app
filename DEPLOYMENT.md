# Инструкции по развертыванию на Render

## Проблема
Ошибка `ModuleNotFoundError: No module named 'app'` возникала потому, что Gunicorn не мог найти модуль `app`.

## Решение
Создан файл `app.py`, который импортирует FastAPI приложение из `main.py`.

## Файлы для развертывания

### 1. app.py
```python
# Импортируем FastAPI приложение из main.py
from main import app

# Экспортируем приложение для Gunicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. Procfile
```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker
```

### 3. runtime.txt
```
python-3.11.0
```

### 4. requirements.txt
Все необходимые зависимости уже включены.

## Переменные окружения для Render

Убедитесь, что в настройках Render установлены следующие переменные окружения:

- `BOT_TOKEN` - токен вашего Telegram бота
- `ADMIN_ID` - ID администратора (число)
- `RENDER_EXTERNAL_URL` - URL вашего приложения на Render (автоматически устанавливается)
- `WEBHOOK_SECRET` - секретный токен для вебхука (опционально)
- `MAX_ATTEMPTS` - максимальное количество попыток (по умолчанию 2)
- `DEBUG` - режим отладки (true/false, по умолчанию false)

## Тестирование

Для локального тестирования запустите:
```bash
python test_app.py
```

Для запуска сервера разработки:
```bash
python app.py
```

## Структура приложения

- `main.py` - основной файл с FastAPI приложением
- `app.py` - точка входа для Gunicorn
- `config.py` - конфигурация
- `custom_methods.py` - пользовательские методы
- `scraper.py` - скрапер данных
- `*.html`, `*.js`, `*.css` - статические файлы веб-интерфейса 