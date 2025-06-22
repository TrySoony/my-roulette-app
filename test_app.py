#!/usr/bin/env python3
"""
Простой тестовый файл для проверки работы приложения
"""
import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import app
    print("✅ Приложение успешно импортировано!")
    print(f"📋 Тип приложения: {type(app)}")
    print(f"🔗 Доступные маршруты:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"   - {route.path}")
except Exception as e:
    print(f"❌ Ошибка при импорте: {e}")
    import traceback
    traceback.print_exc() 