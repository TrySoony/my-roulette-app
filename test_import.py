#!/usr/bin/env python3
"""
Тестовый файл для проверки импорта приложения
"""
import os
import sys

# Устанавливаем фиктивные переменные окружения для тестирования ДО импорта
os.environ['BOT_TOKEN'] = 'test_token'
os.environ['ADMIN_ID'] = '123456789'
os.environ['RENDER_EXTERNAL_URL'] = 'https://test.onrender.com'
os.environ['WEBHOOK_SECRET'] = 'test_secret'
os.environ['MAX_ATTEMPTS'] = '2'
os.environ['DEBUG'] = 'false'

try:
    # Теперь импортируем приложение
    from app import app
    print("SUCCESS: Приложение импортировано успешно!")
    print(f"Type: {type(app)}")
    print(f"Routes count: {len(app.routes)}")
    
    print("\n✅ Все тесты пройдены успешно!")
    
except Exception as e:
    print(f"ERROR: Ошибка при импорте: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 